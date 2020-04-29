odoo.define('maintain.Pager', function (require) {
"use strict";

    var Pager = require('web.Pager');

    var MyPage = Pager.include({
        events: _.extend({}, Pager.prototype.events, {
            // Add more event when click on first and last
            'click .o_pager_first': '_onFirst',
            'click .o_pager_last': '_onLast'
        }),
        init: function () {
            this._super.apply(this, arguments);
        },

        // Add custom
        /**
         * Event when click on first
         */
        _onFirst: function(event){
            event.stopPropagation();

            if (this.state.current_min === 1) {
                return;
            }

            if (this.state.limit === 1) {
                this._changeSelection((this.state.current_min - 1) * -1);
            } else {
                var step = parseInt(this.state.current_min/this.state.limit);

                if (step > 0) {
                    this._changeSelection(step * -1);
                }
            }
        },

        /**
         * Event when click on last
         */
        _onLast: function(event){
            event.stopPropagation();

            if (this.state.limit === 1) {
                if (this.state.current_min === this.state.size) {
                    return;
                }

                var step = this.state.size - this.state.current_min;
                this._changeSelection(step);
            } else {
                var total = parseInt(this.state.size/this.state.limit);
                var step = total - parseInt(this.state.current_min/this.state.limit);

                if (step > 0) {
                    this._changeSelection(step);
                }
            }
        }
    });
    Pager.include(MyPage);
});