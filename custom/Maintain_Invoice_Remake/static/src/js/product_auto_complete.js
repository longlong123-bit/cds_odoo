odoo.define('product.autocomplete.many2one', function (require) {
'use strict';

var FieldMany2One = require('web.relational_fields').FieldMany2One;
var core = require('web.core');
var AutocompleteMixin = require('partner.autocomplete.Mixin');
var field_registry = require('web.field_registry');

var _t = core._t;

var ProductField = FieldMany2One.extend(AutocompleteMixin, {


    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
    },

    /**
     * @override
     * @private
     */
    _renderEdit: function (){
        var matches = this.m2o_value.match(/\[(.*?)\]/);

        if (matches) {
            this.m2o_value = matches[1];
        }
        this._super.apply(this, arguments);
//        this._modifyAutompleteRendering();
    },

    /**
     * @private
     */
    _renderReadonly: function () {

        var matches = this.m2o_value.match(/\[(.*?)\]/);

        if (matches) {
            this.m2o_value = matches[1];
        }
        var escapedValue = _.escape((this.m2o_value || "").trim());
        var value = escapedValue.split('\n').map(function (line) {
            return '<span>' + line + '</span>';
        }).join('<br/>');
        this.$el.html(value);
        if (!this.noOpen && this.value) {
            this.$el.attr('href', _.str.sprintf('#id=%s&model=%s', this.value.res_id, this.field.relation));
            this.$el.addClass('o_form_uri');
        }
        this.$el.removeAttr('href');
       this.$el.replaceWith($('<span>' + this.innerHTML + '</span>'));
    },


});

field_registry.add('product_many2one', ProductField);

return ProductField;
});
