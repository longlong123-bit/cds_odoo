odoo.define('sale.order.custom', function (require) {
"use strict";

    var core = require('web.core');
    var _t = core._t;

    var qweb = core.qweb;
    var concurrency = require('web.concurrency');
    var Context = require('web.Context');
    var session = require('web.session');
    var Dialog = require('web.Dialog');
    var Widget = require('web.Widget');
    var dialogs = require('web.view_dialogs');

    var fieldsSelect = [
        'name',
        'document_no',
        'order_id',
        'shipping_address',
        'expected_date',
        'expiration_date',
        'state',
        'company_id',
        'note',
        'comment',
        'quotation_type',
        'report_header',
        'paperformat_id',
        'paper_format',
        'is_print_date',
        'tax_method',
        'quotations_date',
        'partner_id',
        'partner_name',
        'sales_rep',
        'cb_partner_sales_rep_id',
        'comment_apply',
        'create_date'
    ];

    var QuotationHistoryButton = {
        SEARCH_LIMIT: 322,

        init: function () {
            // this mutex is necessary to make sure some operations are done
            // sequentially, for example, an onchange needs to be completed before a
            // save is performed.
            this.mutex = new concurrency.Mutex();

            // this array is used to accumulate RPC requests done in the same call
            // stack, so that they can be batched in the minimum number of RPCs
            this.batchedRPCsRequests = [];

            this.localData = Object.create(null);
            this._super.apply(this, arguments);
        },

        _onShowExamples: function () {
            var self = this;
//            var dialog = new Dialog(this, {
//                $content: $(qweb.render('KanbanView.ExamplesDialog1', {
//                    examples: this.examples,
//                })),
//                buttons: [{
//                    classes: 'btn-primary float-right',
//                    close: true,
//                    text: _t('Got it'),
//                }],
//                size: "large",
//                title: "Kanban Examples",
//            }).open();

                var prom;
                var search_val = $('[name ="order_id"]').find('input').val();
                var test1 = [1, 2];
                var myArray = {id1: 100, id2: 200, "tag with spaces": 300};
                var test2 = 3;
                prom = self._rpc({
                    model: 'sale.order',
                    method: 'search_order',
//                        args: [search_val, self.SEARCH_LIMIT],
                    kwargs: {
                        args: [test1, test2, myArray],
                        name: search_val,
//                            operator: "ilike",
                        limit: self.SEARCH_LIMIT,
//                            context: context,
                    },
                });
                Promise.resolve(prom).then(function (results) {
                    var dynamicFilters;
                    if (results) {
                        var ids = _.map(results, function (x) {
                            return x[0];
                        });
                        if (search_val !== '') {
                            dynamicFilters = [{
                                description: _.str.sprintf(_t('Name: %s'), search_val),
                                domain: [['id', 'in', ids]],
                            }];
                        }
                    }
                    self._searchCreatePopup("search", false, {}, dynamicFilters);
                });

//            dialog.on('closed', this, function () {
//                self.$input.focus();
//            });
        },

    _searchCreatePopup: function (view, ids, context, dynamicFilters) {
        var options = this._getSearchCreatePopupOptions(view, ids, context, dynamicFilters);

        var dialogSelect = new dialogs.SelectCreateDialog(this, _.extend({}, this.nodeOptions, options));
        dialogSelect.template = 'NewControlPanel';

//        dialogSelect.test_func = function () {
//            alert(123);
//            $( ".btn_search_order" ).click(function() {
//              alert( "click" );
//            });
//        };
//        dialogSelect.test_func();

        dialogSelect.opened().then(function () {
            $( ".btn_search_order" ).click(function() {
              alert( "click" );
            });
        });

        return dialogSelect.open();

//        return new dialogs.SelectCreateDialog(this, _.extend({}, this.nodeOptions, options)).open();

    },
    _getSearchCreatePopupOptions: function(view, ids, context, dynamicFilters) {
        var self = this;
        return {
            res_model: 'sale.order',
//            domain: this.record.getDomain({fieldName: this.name}),
//            context: _.extend({}, this.record.getContext(this.recordParams), context || {}),
            dynamicFilters: dynamicFilters || [],
            title: (view === 'search' ? _t("Search: ") : _t("Create: ")) + _t("Quotation History"),
//            size: 'ultra-large',
            initial_ids: ids,
            initial_view: view,
            disable_multiple_selection: true,
            no_create: !self.can_create,
//            kanban_view_ref: this.attrs.kanban_view_ref,
            on_selected: function (records) {
                self.reinitialize(records[0]);
            },
            on_closed: function () {
                self.activate();
            },
        };
    },

    _getEvalContext: function (element, forDomain) {
        var evalContext = element.type === 'record' ? this._getRecordEvalContext(element, forDomain) : {};

        if (element.parentID) {
            var parent = this.localData[element.parentID];
            if (parent.type === 'list' && parent.parentID) {
                parent = this.localData[parent.parentID];
            }
            if (parent.type === 'record') {
                evalContext.parent = this._getRecordEvalContext(parent, forDomain);
            }
        }
        // Uses "current_company_id" because "company_id" would conflict with all the company_id fields
        // in general, the actual "company_id" field of the form should be used for m2o domains, not this fallback
        if (session.user_context.allowed_company_ids) {
            var current_company = session.user_context.allowed_company_ids[0];
        } else {
            var current_company = session.user_companies ? session.user_companies.current_company[0] : false;
        }
        return _.extend({
            active_id: evalContext.id || false,
            active_ids: evalContext.id ? [evalContext.id] : [],
            active_model: element.model,
            current_date: moment().format('YYYY-MM-DD'),
            id: evalContext.id || false,
            current_company_id: current_company,
        }, session.user_context, element.context, evalContext);
    },

    _getContext: function (element, options) {
        options = options || {};
        var context = new Context(session.user_context);
        context.set_eval_context(this._getEvalContext(element));

        if (options.full || !(options.fieldName || options.additionalContext)) {
            context.add(element.context);
        }
        if (options.fieldName) {
            var viewType = options.viewType || element.viewType;
            var fieldInfo = element.fieldsInfo[viewType][options.fieldName];
            if (fieldInfo && fieldInfo.context) {
                context.add(fieldInfo.context);
            } else {
                var fieldParams = element.fields[options.fieldName];
                if (fieldParams.context) {
                    context.add(fieldParams.context);
                }
            }
        }
        if (options.additionalContext) {
            context.add(options.additionalContext);
        }
        if (element.rawContext) {
            var rawContext = new Context(element.rawContext);
            var evalContext = this._getEvalContext(this.localData[element.parentID]);
            evalContext.id = evalContext.id || false;
            rawContext.set_eval_context(evalContext);
            context.add(rawContext);
        }

        return context.eval();
    },

    reloadData: function (value) {
        var self = this;
        var record = this.model.get(this.handle);
//        var record = this.localData[this.handle];
//        var context = this._getContext(record);
        return this._rpc({
                model: 'sale.order',
                method: 'get_detail_order',
//                model: record.model,
//                method: 'copy',
                args: [value.id, fieldsSelect],
//                context: context,
            })
            .then(function (res_id) {
//                var index = record.res_ids.indexOf(record.res_id);
//                record.res_ids.splice(index + 1, 0, res_id);
                return self.model.load({
////                    fieldsInfo: record.fieldsInfo,
////                    fields: record.fields,
//                    modelName: 'sale.order',
//                    res_id: res_id,
//                    res_ids: [74],
//                    viewType: 'form',
////                    context: context,
            context: record.getContext(),
            fields: record.fields,
            fieldsInfo: record.fieldsInfo,
            modelName: 'sale.order',
                    res_id: value.id,
//            parentID: parentID,
            res_ids: record.res_ids,
            type: 'record',
            viewType: 'form',
                });
            });
    },

    _setValue: function (value, options) {
        value = value || {};

//        var testValue = $( "#test-input-form" ).val();
            return this._rpc({
                model: 'sale.order',
                method: 'set_order',
//                model: record.model,
//                method: 'copy',
                args: [value.id],
//                context: context,
            });
//        var result = this._rpc({
//                    model: 'sale.order',
//                    method: 'get_detail_order',
//                    args: [value.id, fieldsSelect],
//                }).then(function (result) {
//                    // set display value get from result
//                    for (var key in result) {
////                        console.log("key: " + key + " - has value " + result[key]);
//                        switch($('[name ="'+ key +'"]').prop("tagName")) {
//                            case 'SPAN':
//                                $('[name ="'+ key +'"]').text(result[key]);
//                                break;
//                            case 'DIV':
//                                $('[name ="'+ key +'"]').find('input').val(result[key]);
//                                break;
//                            default:
//                                $('[name ="'+ key +'"]').val(result[key]);
//                        }
//                    }
//
//                    // TODO set name ??? :D ???
//                    $('[name ="order_id"]').find('input').val(result['name']);
//                });
    },

    reinitialize: function (value) {
        var self = this;
        return this._setValue(value);
//        return this.reloadData(value).then(function (handle) {
//            self.handle = handle;
//            self._updateEnv();
//            return self._setMode('edit');
//        });
//        return this.reloadData(this.handle)
//            .then(function (handle) {
//                self.handle = handle;
//                self._updateEnv();
//                self._setMode('edit');
//            });
    },

    activate: function (options) {
        if (!this.activeActions.create || this.isReadonly || !this.$el.is(":visible")) {
            return false;
        }
        return true;
    },

        _onTest: function (event) {
                var testValue = $( "#test-input-list" ).val();
//                alert(testValue);
                var testValueResult = this._rpc({
                    model: 'sale.order',
                    method: 'test_js',
                    args: [testValue],
                }).then(function (result) {
                    alert(result);
                    self.$('table')
                        .append(result);
                });
        },
    }
    return QuotationHistoryButton;
});


odoo.define('sale.order.custom.tree', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var QuotationHistoryButton = require('sale.order.custom');
    var viewRegistry = require('web.view_registry');

    var SaleOrderListController = ListController.extend(QuotationHistoryButton, {
        buttons_template: 'SaleOrderListView.buttons',
        events: _.extend({}, ListController.prototype.events, {
            'click .button-test': '_onTest',
        }),
    });

    var SaleOrderListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: SaleOrderListController,
        }),
    });

//    viewRegistry.add('test_button_tree', SaleOrderListView);
});


odoo.define('sale.order.custom.form', function (require) {
'use strict';

    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var FormRenderer = require('web.FormRenderer');
    var viewRegistry = require('web.view_registry');
    var QuotationHistoryButton = require('sale.order.custom');

    var SaleOrderCustomFormController = FormController.extend(QuotationHistoryButton, {
        events: _.extend({}, FormController.prototype.events, {
            'click .quotation-history': '_onShowExamples',
        }),
    });

    var SaleOrderCustomFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: SaleOrderCustomFormController,
        }),
    });

    viewRegistry.add('quotation-custom', SaleOrderCustomFormView);
});
