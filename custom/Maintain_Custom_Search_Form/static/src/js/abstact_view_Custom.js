odoo.define('web.abstact_view_Custom', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Domain = require('web.Domain');
var AbstractView = require('web.AbstractView');


var _t = core._t;
var QWeb = core.qweb;

var Abstact_view_Custom = AbstractView.include({

    searchMenuTypes: ['filter1','filter', 'groupBy', 'favorite'],

    init: function (parent, filters, fields) {
        this._super(parent, filters);
    },

});

AbstractView.include(Abstact_view_Custom);

});
