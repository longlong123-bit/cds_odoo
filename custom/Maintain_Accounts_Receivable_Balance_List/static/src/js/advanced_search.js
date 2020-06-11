odoo.define('Accounts_Receivable_Balance_List.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    // Filter menu in advanced search
    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'res.partner': {
                template: 'accounts_Receivable_balance_list.advanced_search'
            }
        })
    });

    // Handle checked all check box when init screen
    intervalCheckBox = setInterval(handleCheckAllCheckBox, 1000);
    function handleCheckAllCheckBox() {
        content = document.body.getElementsByClassName('o_content');
        if (content.length > 0) {
            check_box_all = $('.o_list_view th.o_list_record_selector input[type=checkbox]');
            if (check_box_all.length > 0) {
                check_box_all_id = check_box_all[0].id;
                if (check_box_all_id) {
                    $('#' + check_box_all_id).trigger('click');
                    $('.o_list_record_selector').css('pointer-events', 'none');
                    clearInterval(intervalCheckBox);
                }
            }
        }
    };
});
