odoo.define('Supplier_Ledger_Inquiry.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['supplier.ledger'] = advancedSearch['supplier.ledger'] || {};
    advancedSearch['supplier.ledger']['supplier_ledger_inquiry_tree'] = {
        template: 'supplier_ledger_inquiry.advanced_search'
    }

    // Filter menu in advanced search
    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});
