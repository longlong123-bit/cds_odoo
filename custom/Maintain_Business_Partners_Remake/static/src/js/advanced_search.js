odoo.define('Partner.Advanced_search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'res.partner': {
                template: 'Partner.advanced_search'
            }
        })
    });
});
