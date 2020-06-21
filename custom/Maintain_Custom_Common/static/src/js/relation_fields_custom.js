odoo.define('web.relational_fields_custom', function (require) {
"use strict";

    var FieldX2Many = require('web.relational_fields');

    var My_FieldX2Many = FieldX2Many.FieldX2Many.include({
        init: function () {
            this._super.apply(this, arguments);
        },

        _onSaveLine: function (ev) {
            var self = this;
            ev.stopPropagation();
            this.renderer.commitChanges(ev.data.recordID).then(function () {
                self.trigger_up('mutexify', {
                    action: function () {
                        return self._saveLine(ev.data.recordID)
                            .then(ev.data.onSuccess)
                            .then(function(){
                                if(typeof self.name !=='undefined'){
                                    if(self.name === 'invoice_line_ids'){
                                        self.trigger_up('toggle_column_order', {
                                            id: self.value.id,
                                            name: 'invoice_custom_line_no',
                                        });
                                    }
                                    if(self.name === 'order_line'){
                                        self.trigger_up('toggle_column_order', {
                                            id: self.value.id,
                                            name: 'quotation_custom_line_no',
                                        });
                                    }
                                }
                            })
                            .guardedCatch(ev.data.onFailure);
                    },
                });
            });
        },


    });
    FieldX2Many.FieldX2Many.include(My_FieldX2Many);
});