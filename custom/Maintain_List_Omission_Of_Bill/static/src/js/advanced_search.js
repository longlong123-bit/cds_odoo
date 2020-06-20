odoo.define('List_Omission_Of_Bill.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['omission.bill'] = advancedSearch['omission.bill'] || {};
    advancedSearch['omission.bill']['list_omission_of_bill_tree'] = {
        template: 'list_omission_of_bill.advanced_search'
    }

    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});
