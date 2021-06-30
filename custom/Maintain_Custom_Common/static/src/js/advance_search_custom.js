odoo.define('web.AdvanceSeachCustom', function (require) {
"use strict";
    var config = require('web.config');
    var core = require('web.core');
    var _t = core._t;
    var view_registry = require('web.view_registry');
    var select_create_controllers_registry = require('web.select_create_controllers_registry');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;
    var dom = require('web.dom');
    var Dialog = require('web.Dialog');
    var ViewDialog = Dialog.extend({
        xmlDependencies: ['./Maintain_Widget_Relation_Field/static/src/xml/dialog.xml'],
        custom_events: _.extend({}, Dialog.prototype.custom_events, {
            push_state: '_onPushState',
        }),

        _willStart: function () {
            var proms = [];
            if (this.xmlDependencies) {
                proms.push.apply(proms, _.map(this.xmlDependencies, function (xmlPath) {
                    return ajax.loadXML(xmlPath, core.qweb);
                }));
            }
            if (this.jsLibs || this.cssLibs || this.assetLibs) {
                proms.push(ajax.loadLibs(this));
            }
            return Promise.all(proms);
        },

        /**
         * Wait for XML dependencies and instantiate the modal structure (except
         * modal-body).
         *
         * @override
         */
        willStart: function () {
            var self = this;
            return this._willStart().then(function () {
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
                if (self.renderFooter) {
                  self.$footer = self.$modal.find(".modal-footer");
                  self.set_buttons(self.buttons);
                }

                self.$modal.find('.modal-dialog').addClass('modal-widget');
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
        /**
         * If the list view editable, just let the event bubble. We don't want to
         * open the record in this case anyway.
         *
         * @override
         * @private
         */
        _onRowClicked: function (ev) {
          return;
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

    var SearchDialog = ViewDialog.extend({
        custom_events: _.extend({}, ViewDialog.prototype.custom_events, {
            select_record: function (event) {
              window.cc.push(event.data.id);
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
            this.buttons = [{text: _t("Select"), select: true}];
            this.withSearchBar = false;
            this.searchMenuTypes = false;
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
                        // Hien-TT custom start
                        $(fragment).find('.o_list_view').addClass('dialog_show');
                        // Hien-TT custom end
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
                    hasSelectors: true,
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
                hasSelectors: true
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

        /**
         * Render and set the given buttons into a target element
         *
         * @private
         * @param {jQueryElement} $target The destination of the rendered buttons
         * @param {Array} buttons The array of buttons to render
         */
        _setButtonsTo($target, buttons) {
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
                    // Hien-TT custom start
                    if (buttonData.select) {
                      self.onForceClose = false;
                      self.getParent().getParent().getParent().getChildren().forEach(function (child){
                          if (child.name == 'copy_history_from') {
                            child._setValue(self.options.res_model);
                            child._render();
                          }
                      })
                      self.getParent().getParent().getParent().getChildren().forEach(function (child){
                        if (child.name == 'copy_history_item') {
                            child._setValue(self.viewController.getSelectedIds().toString());
                            child._render();
                        }
                      })
                      Promise.resolve(def).then(self.close.bind(self)).guardedCatch(self.close.bind(self));
                    }
                    // Hien-TT custom end
                });
                if (self.technical) {
                    $target.append($button);
                } else {
                    $target.prepend($button);
                }
            });
        },
      });

    var FilterMenu = require('web.FilterMenu_free');

    var FilterMenu = FilterMenu.include({
        events: _.extend({}, FilterMenu.prototype.events, {
            'click .o_apply_filter_customer_code': '_customFillter',
        }),
        /**
         * @private
         * @param {OdooEvent} ev
         */
        _customFillter: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            // get current context (language, param,...)
            // var context = {tree_view_ref:'account.view_move_line_tree_grouped_general'};
            // var domain = [["exclude_from_invoice_tab", "=", false]];
            var context;
            var domain;
            // new dialog and show
            new SearchDialog(this, {
                    no_create: true,
                    readonly: true,
                    res_model: "res.partner",
                    domain: domain,
                    view_type:'list',
                    context: context
                    // disable_multiple_selection: true
                }).open();
        },
    //         /**
    //  * @private
    //  * @param {MouseEvent} ev
    //  */
    // _onApplyClick: function (ev) {
    //     alert("dm4");
    //     ev.stopPropagation();
    //     this._commitSearch();
    // },
    });
    // FilterMenu.prototype._onApplyClick =  function (ev) {
    //     alert("dm4");
    //     ev.stopPropagation();
    //     this._commitSearch();
    // };
    return FilterMenu;
});