odoo.define('Order.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'order.management': {
                'order.management.tree': {template: 'order.advanced_search'},
                'order.management.search': {template: 'order.advanced_search'},
            },
            'order.management.line': {
                'order.management.line.tree': {template: 'order_line.advanced_search'},
                'order.management.line.search': {template: 'order_line.advanced_search'},
            }
        })
    });
});