odoo.define('custom_module.report', function(require){
    "use strict";
    var Widget = require('web.Widget');

    Widget.include({
        events: {
            'click .o_report_open_pdf': '_onPrintReport'
        },
        iframe: null,
        isWaiting: false,

        /**
         * Init
         */
        init: function(){
            this._super.apply(this, arguments);
        },

        /**
         * Print
         */
        _print: function(){
            this.iframe.focus();
            this.iframe.contentWindow.print();
            this.isWaiting = false;
        },

        /**
         * On print report
         */
        _onPrintReport: function(e){
            e.preventDefault();

            if (this.isWaiting) {
                return;
            }

            this.isWaiting = true;

            if (this.iframe) {
                this._print(this.iframe);
            } else {
                this.iframe = $(this).closest('.o_action').find('.o_content iframe');
                this.iframe.onload = function() {
                  setTimeout(function() {
                    this._print();
                  }, 1);
                };
            }
        }
    });
});
