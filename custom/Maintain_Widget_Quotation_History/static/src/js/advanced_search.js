odoo.define('Maintain_Widget_Quotation_History.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var alias = _.extend({}, FilterMenu.prototype.alias || {});
    alias.view = alias.view || {};
    alias.view['sale.order.list.select'] = 'sale.order.custom.tree';

    FilterMenu.include({
        alias: alias
    });
});
