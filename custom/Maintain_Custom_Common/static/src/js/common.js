odoo.define('common.js', function (require) {
"use strict";

    $(document).on('change',$("invoice_create select[name='x_invoicelinetype']"),function(){

        var amount = $(".invoice_create span[name='invoice_custom_lineamount']");
        var dv =  $(".invoice_create select[name='x_invoicelinetype']");
        var q = $("input[name='quantity']");
        if('"通常"'.localeCompare(dv.val())){
            amount.css("color", "red");
            q.css("color", "red");

        }else{
            amount.css("color", "black");
            q.css("color", "black");
        }
        return;
    });

    $(document).on('change',".invoice_create input[name='discount']",function(){
        var value =  $(".invoice_create input[name='discount']");
        var dv = $(".invoice_create span[name='invoice_custom_discountunitprice']");
        if(value.val()>0){

            dv.attr("style","color:red;");
        }else{
            dv.attr("style","color:black;");
        }
    });
});