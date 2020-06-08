odoo.define('Collation_History.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'account.move': {
                template: 'collation_history.advanced_search'
            }
        })
    });
});
