odoo.define('Maintain_Widget_Relation_Field.search_field', function(require){
    'use strict';
    var AbstractField = require('web.AbstractField');
    var registry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');

    // For dialog
    var Dialog = require('web.Dialog');
    var dialogs = require('web.view_dialogs');
    var config = require('web.config');
    var view_registry = require('web.view_registry');
    var select_create_controllers_registry = require('web.select_create_controllers_registry');
    var dom = require('web.dom');
    var _t = core._t;

    // custom ViewDialog
    var ViewDialog = Dialog.extend({
        xmlDependencies: ['/Maintain_Widget_Relation_Field/static/src/xml/dialog.xml'],
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
                self.$modal = $(QWeb.render('Dialog_Widget_Relation_Field', {
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

                self.$modal.find('.modal-dialog').addClass('modal-widget modal-widget-relation-field');
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
        }
    });

    var SelectCreateDialog = ViewDialog.extend({
        custom_events: _.extend({}, ViewDialog.prototype.custom_events, {
            select_record: function (event) {
                var parent = this.getParent();
                var options = parent._getWidgetOptions();
                var state = this.viewController.renderer.state;

                for (var i = 0; i < state.count; i++) {
                    var data = state.data[i];

                    if (data && data.ref === event.data.id) {
                        parent._setValue(data.data[options.column]);
                    }
                }

                this.close();
            }
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

        // open dialig
        open: function () {
            var self = this;
            var _super = this._super.bind(this);

            var viewRefID1 = this.viewType === 'kanban' ?
                (this.options.kanban_view_ref && JSON.parse(this.options.kanban_view_ref) || false) : false;

            return this.loadViews(this.res_model, this.context, [[viewRefID1, this.viewType], [false, 'search']], {})
                .then(this.setup.bind(this))
                .then(function (fragment) {
                    self.opened().then(function () {
                        var _o_paging;

                        fragment.querySelectorAll(".o_cp_pager").forEach(function(c){
                            _o_paging = c;
                        });

                        $(fragment).find('.o_cp_controller .o_cp_left').empty();

                        // append all DOM to dialog
                        dom.append(self.$el, fragment, {
                            callbacks: [{widget: self.viewController}],
                            in_DOM: true,
                        });
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
                hasSelectors: false
            }));
            view.setController(selectCreateController);

            return view.getController(this).then(function (controller) {
                self.viewController = controller;
                return self.viewController.appendTo(fragment);
            }).then(function () {
                return fragment;
            });
        },

        close: function () {
            this._super.apply(this, arguments);
            this.on_closed();
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

        create_edit_record: function(){}
    });

    /**
     * =============================================================================
     * Widget generate input and button to search data
     * When input text then call to check is exactly data
     * if is not, then open dialog
     */
    var Widget = AbstractField.extend({
        template : "refer_field",

        events : {
            'click .o_button_refer_field': '_onClickButton',
            'click .o_input_refer_field': '_onClickInput',
            'keyup .o_input_refer_field': '_onKeyupInput',
            'blur .o_input_refer_field': '_onBlurInput',
        },

        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
        },

        /**
         * Get display field
         */
        _getWidgetOptions: function(){
            return this.attrs.options;
        },

        /**
         * Render when click on row and open editable
         * Render with template and append value
         */
        _renderEdit: function(){
            if (this.$el.find('input').length == 0) {
                var html = QWeb.render(this.template, this);
                this.$el.html($(html).html());
            }

            if (this.record.data[this.name]) {
                this.$el.find('input').val(this.record.data[this.name]);
            }
        },

        /**
         * Render when click outside row, just display, can not edit
         */
        _renderReadonly: function(){
            this.$el.html('<span></span>');
            this.$el.find('> span').text(this.record.data[this.name] || '');
        },

        /**
         * Check data
         */
        _checkData: function(e, ref){
            var s = this;

            if (this.value == e.target.value) {
                return;
            }

            // Call to server
            rpc.query({
                model: ref.model,
                method: 'search_read',
                domain: [[ref.column, '=', e.target.value]]
            }).then(function(res){
                if (res.length > 0) {
                    s._setValue(res[0][ref.column]);
                } else {
                    s._openDialogSearch();
                }
            });
        },

        /**
         * Event when click on button, then open dialog search
         */
        _onClickButton: function(e){
            e.stopPropagation();
            e.preventDefault();
            this._openDialogSearch();
        },

        /**
         * Event when click on input, stop all
         */
        _onClickInput: function(e){
            e.stopPropagation();
            e.preventDefault();
        },

        /**
         * Event when keyup on input
         * check if is enter then check data
         */
        _onKeyupInput: function(e){
            var options = this._getWidgetOptions();

            if (options.search_input && (e.which === $.ui.keyCode.ENTER || e.which === $.ui.keyCode.TAB)) {
                this._checkData(e, options);
            }
        },

        /**
         * Unfocus
         */
        _onBlurInput: function(e){
            var options = this._getWidgetOptions();

            if (options.search_input) {
                this._checkData(e, options);
            } else {
                this._setValue(e.target.value);
            }
        },

        /**
         * Open dialog search
         */
        _openDialogSearch: function(){
            // get current context (language, param,...)
            var context = this.record.getContext(this.recordParams);
            var ref = this._getWidgetOptions();
            var searchVal = this.$el.find('input').val();
            var filters = null;

            if (searchVal !== '') {
                filters = [{
                    description: _.str.sprintf(_t('Quick search: %s'), searchVal),
                    domain: [[ref.column, 'ilike', searchVal]],
                }];
            }

            // new dialog and show
            new SelectCreateDialog(this, {
                    no_create: true,
                    readonly: true,
                    res_model: ref.model,
                    domain: null,
                    dynamicFilters: filters,
                    view_type:'list',
                    context: context,
                }).open();
        }
    });

    registry.add('refer_field', Widget);
    return Widget;
});