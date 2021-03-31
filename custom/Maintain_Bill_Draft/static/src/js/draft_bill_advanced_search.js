odoo.define('draft_bill.Advanced_Search', function (require) {
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['bill.info.draft'] = advancedSearch['bill_info_draft'] || {};
    advancedSearch['bill.info.draft']['bm.draft.bill.tree'] = {
        template: 'draft_bill.advanced_search'
    }

    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});