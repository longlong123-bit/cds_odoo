odoo.define('Collation_History.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['bill.info'] = advancedSearch['bill.info'] || {};
    advancedSearch['bill.info']['collation.history.tree.view'] = {
        template: 'collation_history.advanced_search'
    }
    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});




