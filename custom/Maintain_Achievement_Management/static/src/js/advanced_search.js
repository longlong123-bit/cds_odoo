odoo.define('Achievement_Management.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');
    var advancedSearch = _.extend({}, FilterMenu.prototype.advancedSearch || {});
    advancedSearch['sales.achievement.employee'] = advancedSearch['sales.achievement.employee'] || {};
    advancedSearch['sales.achievement.customer'] = advancedSearch['sales.achievement.customer'] || {};
    advancedSearch['sales.achievement.customer.business'] = advancedSearch['sales.achievement.customer.business'] || {};
    advancedSearch['sales.achievement.customer.employee'] = advancedSearch['sales.achievement.customer.employee'] || {};
    advancedSearch['sales.achievement.business'] = advancedSearch['sales.achievement.business'] || {};
    advancedSearch['sales.achievement.employee']['sales_achievement_view_employee'] = {
        template: 'sales_achievement_employee.advanced_search'
    };
    advancedSearch['sales.achievement.customer']['sales_achievement_view_customer'] = {
        template: 'sales_achievement_customer.advanced_search'
    },
        advancedSearch['sales.achievement.customer.business']['sales_achievement_view_customer_business'] = {
        template: 'sales_achievement_customer_business.advanced_search'
    },
        advancedSearch['sales.achievement.customer.employee']['sales_achievement_view_customer_employee'] = {
        template: 'sales_achievement_customer_employee.advanced_search'
    },
        advancedSearch['sales.achievement.business']['sales_achievement_view_business'] = {
        template: 'sales_achievement_business.advanced_search'
    }

    // Filter menu in advanced search
    FilterMenu.include({
        advancedSearch: advancedSearch
    });
});
