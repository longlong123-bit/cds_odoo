odoo.define('Product.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'product.product': {
                template: 'Product.advanced_search'
            }
        })
    });
});
