odoo.define('Accounts_Receivable_Balance_List.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'res.partner': {
                template: 'accounts_Receivable_balance_list.advanced_search'
            }
        })
    });
});
