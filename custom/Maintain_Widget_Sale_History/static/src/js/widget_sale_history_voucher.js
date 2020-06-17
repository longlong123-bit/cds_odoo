odoo.define('Maintain_Sale_History.Voucher', function (require) {
'use strict';
var select_create_controllers_registry = require('web.select_create_controllers_registry');
var FieldMany2One = require('web.relational_fields').FieldMany2One;
var core = require('web.core');
var AutocompleteMixin = require('partner.autocomplete.Mixin');
var field_registry = require('web.field_registry');
var widgetRegistry = require('web.widget_registry');
var view_registry = require('web.view_registry');
var dom = require('web.dom');
var config = require('web.config');
var Widget = require('web.Widget');
var datepicker = require('web.datepicker');
var QWeb = core.qweb;

    var Dialog = require('web.Dialog');
    var dialogs = require('web.view_dialogs');
    var rpc = require('web.rpc');

var _t = core._t;


// Custom field many2one
var VoucherHistory = FieldMany2One.extend({
    template : "template_many2one_history_widget_voucher",
    //Binding Events
        events : {
            'click .show_voucher_history_dialog' : 'open',
        },

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
    },

    // method when click button show dialog sale history
    open: function(event){
        event.stopPropagation();
        // get current context (language, param,...)
        var context = this.record.getContext(this.recordParams);

        // new dialog and show
        new SelectCreateDialog(this, {
                no_create: true,
                readonly: true,
                res_model: 'account.move',
                domain: null,
                view_type:'list',
                context: context,
            }).open();
    }
});

// custom ViewDialog
var ViewDialog = Dialog.extend({
    xmlDependencies: ['/Maintain_Widget_Sale_History/static/src/xml/dialog_custom_voucher.xml'],
    custom_events: _.extend({}, Dialog.prototype.custom_events, {
        push_state: '_onPushState',
    }),
    /**
     * Wait for XML dependencies and instantiate the modal structure (except
     * modal-body).
     *
     * @override
     */
    willStart: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            // Render modal once xml dependencies are loaded
            self.$modal = $(QWeb.render('Dialog_Voucher_Custom', {
                fullscreen: self.fullscreen,
                title: self.title,
                subtitle: self.subtitle,
                technical: self.technical,
                renderHeader: self.renderHeader,
                renderFooter: self.renderFooter,
            }));
            switch (self.size) {
                case 'ultra-large':
                    self.$modal.find('.modal-dialog').addClass('modal-ultra');
                    break;
                case 'extra-large':
                    self.$modal.find('.modal-dialog').addClass('modal-xl');
                    break;
                case 'large':
                    self.$modal.find('.modal-dialog').addClass('modal-lg');
                    break;
                case 'small':
                    self.$modal.find('.modal-dialog').addClass('modal-sm');
                    break;
            }

            self.$modal.find('.modal-dialog').addClass('modal-widget');

            if (self.renderFooter) {
                self.$footer = self.$modal.find(".modal-footer");
                self.set_buttons(self.buttons);
            }
            self.$modal.on('hidden.bs.modal', _.bind(self.destroy, self));
        });
    },
    /**
     * @constructor
     * @param {Widget} parent
     * @param {options} [options]
     * @param {string} [options.dialogClass=o_act_window]
     * @param {string} [options.res_model] the model of the record(s) to open
     * @param {any[]} [options.domain]
     * @param {Object} [options.context]
     */
    init: function (parent, options) {
        options = options || {};
        options.fullscreen = config.device.isMobile;
        options.dialogClass = options.dialogClass || '' + ' o_act_window';

        this._super(parent, $.extend(true, {}, options));

        this.res_model = options.res_model || null;
        this.domain = options.domain || [];
        this.context = options.context || {};
        this.options = _.extend(this.options || {}, options || {});
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * We stop all push_state events from bubbling up.  It would be weird to
     * change the url because a dialog opened.
     *
     * @param {OdooEvent} event
     */
    _onPushState: function (event) {
        event.stopPropagation();
    },

    set_buttons: function (buttons,cp) {
        var self = this;
        self._setButtonsTo(this.$footer, buttons,cp);
    },

    _setButtonsTo($target, buttons,cp) {
        var self = this;
        $target.empty();
        _.each(buttons, function (buttonData) {
            var $button = dom.renderButton({
                attrs: {
                    class: buttonData.classes || (buttons.length > 1 ? 'btn-secondary' : 'btn-primary'),
                    disabled: buttonData.disabled,
                },
                icon: buttonData.icon,
                text: buttonData.text,
            });
            $button.on('click', function (e) {
                var def;
                if (buttonData.click) {
                    def = buttonData.click.call(self, e);
                }
                if (buttonData.close) {
                    self.onForceClose = false;
                    Promise.resolve(def).then(self.close.bind(self)).guardedCatch(self.close.bind(self));
                }
            });
            if(buttonData.classes!='btn-secondary o_search_button_search'){
                if (self.technical) {
                    $target.append($button);
                } else {
                    $target.prepend($button);
                }
            }else{
                var hasButtonSearch = $('.search_form').find('.o_search_button_search');
                if(hasButtonSearch.length==0){
                    $('.search_form').append($button);
                    self.render_datepicker('search_sale_date_from');
                    self.render_datepicker('search_sale_date_to');
                }
            }
            $('.cp_paging').html(cp);

        });
    },
});

var SelectCreateDialog = ViewDialog.extend({
    custom_events: _.extend({}, ViewDialog.prototype.custom_events, {
        select_record: function (event) {
            var args = [
                    [['id', '=',event.data.id]]
                ];
            rpc.query({
                    model: 'account.move',
                    method: 'search_read',
                    args: args,
                })
        },
        selection_changed: function (event) {
            event.stopPropagation();
            this.$footer.find(".o_select_button").prop('disabled', !event.data.selection.length);
        },
    }),

    /**
     * options:
     * - initial_ids
     * - initial_view: form or search (default search)
     * - list_view_options: dict of options to pass to the List View
     * - on_selected: optional callback to execute when records are selected
     * - disable_multiple_selection: true to allow create/select multiple records
     * - dynamicFilters: filters to add to the searchview
     */
    init: function () {
        this._super.apply(this, arguments);
        _.defaults(this.options, { initial_view: 'search' });
        this.on_selected = this.options.on_selected || (function () {});
        this.on_closed = this.options.on_closed || (function () {});
        this.initialIDs = this.options.initial_ids;
        this.viewType = arguments[1].view_type;
        this.size = 'ultra-large';
        this.ending = false;
    },

    // render date picker
    render_datepicker: function(name){
        this.create_new_widget(name);

    },

    // create new widget date picker
    create_new_widget: function (name) {
        this[name] = new (this._get_widget_class())(this,{format: "YYYY-MM-DD"});
        this[name].appendTo($('.'+name));
    },

    // create new Class date picker
    _get_widget_class: function () {
        return datepicker.DateTimeWidget;
    },

    // get condition search in form (in dialog_custom_voucher.xml)
    _getSearchFilter_Sale_History: function(){
        var domain = [];

        var f_search_document_no_from_val = $('input[name="search_document_no_from"]').val();
        if (f_search_document_no_from_val!=''){
            var f_document_no_from = ["x_studio_document_no", ">=",f_search_document_no_from_val];
            domain.push(f_document_no_from)
        }

        var f_document_no_to_val = $('input[name="search_document_no_to"]').val();
        if (f_document_no_to_val!=''){
            var f_document_no_to = ["x_studio_document_no", "<=",f_document_no_to_val];
            domain.push(f_document_no_to)
        }

        var f_userinput_id_val = $('input[name="search_input_person"]').val();
        if (f_userinput_id_val!=''){
            var f_userinput_id = ["x_userinput_id", "ilike",f_userinput_id_val];
            domain.push(f_userinput_id)
        }

        var f_sale_date_from_val = $('.search_sale_date_from').find('input').val()
        if (f_sale_date_from_val!=''){
            var f_sale_date_from = ["x_studio_date_invoiced", ">=",f_sale_date_from_val];
            domain.push(f_sale_date_from)
        }

        var f_sale_date_to_val = $('.search_sale_date_to').find('input').val()
        if (f_sale_date_to_val!=''){
            var f_sale_date_to = ["x_studio_date_invoiced", "<=",f_sale_date_to_val];
            domain.push(f_sale_date_to)
        }

        var f_customer_code_val = $('input[name="search_customer_code"]').val();
        if (f_customer_code_val!=''){
            var f_customer_code = ["x_customer_code_for_search", "ilike",f_customer_code_val];
            domain.push(f_customer_code)
        }

        var f_customer_name_val = $('input[name="search_customer_name"]').val();
        if (f_customer_name_val!=''){
            var f_customer_name = ["x_studio_name", "ilike",f_customer_name_val];
            domain.push(f_customer_name)
        }

        // return domain
        // domain example: [['filed','operator','search condition data'],[...],....]
        return domain;
    },

    // method search
    _search_sale_history: function () {
        event.stopPropagation();
        var self = this;
        // remove all body dialog
        $('.o_act_window').html('');

        // get search domain
        this.domain = this._getSearchFilter_Sale_History();

        // get viewRefID
        var viewRefID = this.viewType === 'kanban' ?
            (this.options.kanban_view_ref && JSON.parse(this.options.kanban_view_ref) || false) : false;

        // loadview
        return this.loadViews(this.res_model, this.context, [[viewRefID, this.viewType], [false, 'search']], {})
            .then(this.setup.bind(this))
            .then(function (fragment) {
                self.opened().then(function () {
                    var _o_paging;

                    // get paging DOM
                    fragment.querySelectorAll(".o_cp_pager").forEach(function(c){
                        _o_paging = c;
//                        _o_paging.style.cssFloat = 'right';
//                        c.parentNode.removeChild(c);
                    });
//
//                    // remove all control DOM
//                    fragment.querySelectorAll(".o_control_panel").forEach(function(c){
//                        c.parentNode.removeChild(c);
//                    });

                    // custom change checkbox --> radio
                    $(fragment).find('.o_content input[type="checkbox"]').each(function(i, c){
                        //var t = c;
                        c.type ='radio';
                        c.name = 'radio_custom';
                        c.className='';
                        var label_remove = c.parentNode.getElementsByTagName("label")[0];
                        c.parentNode.removeChild(label_remove);
                    });

                    $(fragment).find('.o_data_row').click(function(e){
                        if (e.target.name === 'radio_custom') {
                            return;
                        }

                        e.stopPropagation();
                        e.preventDefault();

                        var radio = $(this).find('input[type="radio"]');

                        if ($(this).find('input[type="radio"]').is(':checked')) {
                            radio.prop('checked', false);
                        }
                        else {
                            radio.prop('checked', true);
                        }

                        radio.change();
                    });

                    // custom remove footer table
                    $(fragment).find('.o_content th').each(function(i, c){
                        if(c.className==='o_list_record_selector'){
                            c.innerHTML='';
                        }
                        c.style.padding = '0px';

                    });
                    fragment.querySelectorAll(".o_list_record_selector").forEach(function(c){
                       c.style.padding = '3px';
                    });

                    // custom remove footer table
                     fragment.querySelectorAll("tfoot").forEach(function(c){
                        c.parentNode.removeChild(c);
                    });

                    // add class dialog_show (to handle event (click,...) in list)
                    fragment.querySelectorAll(".forward_edit").forEach(function(c){
                        c.classList.add('dialog_show');

                    });

                    // append all DOM to dialog
                    dom.append(self.$el, fragment, {
                        callbacks: [{widget: self.viewController}],
                        in_DOM: true,
                    });

                    // set button
//                    _o_paging.querySelectorAll(".o_pager").forEach(function(c){
//                         c.style.cssFloat = 'right';
//                    });
                    self.set_buttons(self.__buttons,_o_paging.innerHTML);
                });
            });
    },

    // open dialig
    open: function () {

        if (this.options.initial_view !== "search") {
            return this.create_edit_record();
        }
        var self = this;
        var _super = this._super.bind(this);

        var viewRefID1 = this.viewType === 'kanban' ?
            (this.options.kanban_view_ref && JSON.parse(this.options.kanban_view_ref) || false) : false;

        return this.loadViews(this.res_model, this.context, [[viewRefID1, this.viewType], [false, 'search']], {})
            .then(this.setup.bind(this))
            .then(function (fragment) {
                self.opened().then(function () {
                    // this block code and  _search_sale_history...loadviews block code are the same --> need refactor to function
                    var _o_paging;

                     get paging DOM
                    fragment.querySelectorAll(".o_cp_pager").forEach(function(c){
                        _o_paging = c;
//                        _o_paging.style.cssFloat = 'right';
//                        c.parentNode.removeChild(c);
                    });
//
//                    // remove all control DOM
//                    fragment.querySelectorAll(".o_control_panel").forEach(function(c){
//                        c.parentNode.removeChild(c);
//                    });

                    // custom change checkbox --> radio
                    $(fragment).find('.o_content input[type="checkbox"]').each(function(i, c){
                        //var t = c;
                        c.type ='radio';
                        c.name = 'radio_custom';
                        c.className='';
                        var label_remove = c.parentNode.getElementsByTagName("label")[0];
                        c.parentNode.removeChild(label_remove);
                    });

                    $(fragment).find('.o_data_row').click(function(e){
                        if (e.target.name === 'radio_custom') {
                            return;
                        }

                        e.stopPropagation();
                        e.preventDefault();

                        var radio = $(this).find('input[type="radio"]');

                        if ($(this).find('input[type="radio"]').is(':checked')) {
                            radio.prop('checked', false);
                        }
                        else {
                            radio.prop('checked', true);
                        }

                        radio.change();
                    });

                    // custom remove footer table
                    $(fragment).find('.o_content th').each(function(i, c){
                        if(c.className==='o_list_record_selector'){
                            c.innerHTML='';
                        }
                        c.style.padding = '0px';

                    });
                    fragment.querySelectorAll(".o_list_record_selector").forEach(function(c){
                       c.style.padding = '3px';
                    });

                    // custom remove footer table
                     fragment.querySelectorAll("tfoot").forEach(function(c){
                        c.parentNode.removeChild(c);
                    });

                    // add class dialog_show (to handle event (click,...) in list)
                    fragment.querySelectorAll(".forward_edit").forEach(function(c){
                        c.classList.add('dialog_show');

                    });

                    // append all DOM to dialog
                    dom.append(self.$el, fragment, {
                        callbacks: [{widget: self.viewController}],
                        in_DOM: true,
                    });

                    // set button
//                    _o_paging.querySelectorAll(".o_pager").forEach(function(c){
//                         c.style.cssFloat = 'right';
//                    });
                    self.set_buttons(self.__buttons,_o_paging.innerHTML);
                });
                return _super();
            });
    },

    setup: function (fieldsViews) {

        // this block does not need --> refactor
        var vt ='';
        if(typeof fieldsViews.form!= 'undefined'){
            vt = 'form';
        }else{
            vt = 'list'
        }

        var self = this;
        var fragment = document.createDocumentFragment();

        var domain = this.domain;
        if (this.initialIDs) {
            domain = domain.concat([['id', 'in', this.initialIDs]]);
        }
        var ViewClass = view_registry.get(vt);
        var viewOptions = {};
        var selectCreateController;
        if (this.viewType === 'list' && vt=='list') { // add listview specific options
            _.extend(viewOptions, {
                hasSelectors: !this.options.disable_multiple_selection,
                readonly: true,

            }, this.options.list_view_options);
            selectCreateController = select_create_controllers_registry.SelectCreateListController;
        }
        if (this.viewType === 'kanban') {
            _.extend(viewOptions, {
                noDefaultGroupby: true,
                selectionMode: this.options.selectionMode || false,
            });
            selectCreateController = select_create_controllers_registry.SelectCreateKanbanController;
        }

        var view = new ViewClass(fieldsViews[vt], _.extend(viewOptions, {
            action: {
                controlPanelFieldsView: fieldsViews.search,
                help: _.str.sprintf("<p>%s</p>", _t("No records found!")),
            },
            action_buttons: false,
            dynamicFilters: this.options.dynamicFilters,
            context: this.context,
            domain: domain,
            modelName: this.res_model,
            withBreadcrumbs: false,
            withSearchPanel: false,
        }));
        view.setController(selectCreateController);
        return view.getController(this).then(function (controller) {
            self.viewController = controller;
            // render the footer buttons
            self._prepareButtons();
            return self.viewController.appendTo(fragment);
        }).then(function () {
            return fragment;
        });
    },
    close: function () {
        this._super.apply(this, arguments);
        this.on_closed();
    },
    create_edit_record: function () {
        var self = this;
        var dialog = new FormViewDialog(this, _.extend({}, this.options, {
            on_saved: function (record) {
                var values = [{
                    id: record.res_id,
                    display_name: record.data.display_name || record.data.name,
                }];
                self.on_selected(values);
            },
        })).open();
        dialog.on('closed', this, this.close);
        return dialog;
    },
    /**
     * @override
     */
    _focusOnClose: function() {
        var isFocusSet = false;
        this.trigger_up('form_dialog_discarded', {
            callback: function (isFocused) {
                isFocusSet = isFocused;
            },
        });
        return isFocusSet;
    },

    /**
     * prepare buttons for dialog footer based on options
     *
     * @private
     */
    _prepareButtons: function () {
        this.__buttons = [{
            text: _t("Cancel"),
            classes: 'btn-secondary o_form_button_cancel',
            close: true,
        },
        {
            text: _t("Search"),
            classes: 'btn-secondary o_search_button_search',
            click: this._search_sale_history.bind(this),

        }
        ];
        if (!this.options.no_create) {
            this.__buttons.unshift({
                text: _t("Create"),
                classes: 'btn-primary',
                click: this.create_edit_record.bind(this)
            });
        }
        if (!this.options.disable_multiple_selection) {
            this.__buttons.unshift({
                text: _t("Select"),
                classes: 'btn-primary o_select_button',
                disabled: true,
                close: true,

                // event when click select button to return data to parent
                click: function () {
                    // get records
                    var records = this.viewController.getSelectedRecords();

                    // get id
                    var values = _.map(records, function (record) {
                        return {
                            id: record.res_id,
                            display_name: record.data.display_name,
                        };
                    });

                    // reinitialize parent
                    this.getParent().reinitialize(values[0]);
                },
            });
        }
    },
});

// registry widget
field_registry.add('Maintain_Sale_History.Voucher', VoucherHistory);

// return widget
return VoucherHistory;
});