// Show detail of tree view when click on row of tree
odoo.define('Maintain_Custom_Common.show_lines', function(require){
    "use strict";

    var control = require('web.ListController');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var QWeb = core.qweb;

    control.include({
        /**
         * Render line
         */
        _renderTemplate: function($target, data){
            var html = QWeb.render(data.template, {records: data.records});
            $target.append(html);
        },

        /**
         * Render lines
         */
        _renderRowOfLines: function(id, data){
            var $target = $('tr[data-id="'+id+'"]');

            // Create new row
            var $tr = $('tr.row-lines[data-ref="'+ id +'"]');

            if ($tr.length === 0) {
                $tr = $('<tr></tr>');
                $tr.attr({
                    'data-ref': $target.attr('data-id'),
                    'class': 'row-lines'
                });
            } else {
                $tr.removeClass('empty').empty();
            }

            $tr.css({display: 'none'});

            if (data.records.length > 0) {
                $tr.append('<td></td>');

                // Create column contains table lines
                var $td = $('<td></td>');
                $td.attr({
                    colspan: $target.find('td').length - 1
                });
                $tr.append($td);

                this._renderTemplate($td, data);
            } else {
                $tr.addClass('empty');
            }

            // Append row to parent table
            $target.after($tr);
            this._toggleRow(id);
        },

        /**
         * Toggle display row
         */
        _toggleRow: function(id){
            var $icon = $('tr[data-id="'+id+'"] .o_button_line i');
            var $checkRow = $('tr[data-ref="'+id+'"]');

            if (!$checkRow.hasClass('empty')) {
                $checkRow.toggle();

                if ($checkRow.css('display') == 'none') {
                    $icon.removeClass('fa-toggle-down').addClass('fa-toggle-right');
                } else {
                    $icon.removeClass('fa-toggle-right').addClass('fa-toggle-down');
                }
            }
        },

        /**
         * on button clicked
         */
        _onButtonClicked: function($ev){
            $ev.stopPropagation();

            if ($ev.data.attrs.class === 'o_button_line') {
                // Check if row is exists
                var $checkRow = $('tr.row-lines[data-ref="'+$ev.data.record.id+'"]');
                var self = this;

                if ($checkRow.length > 0) {
                    if ($checkRow.css('display') != 'none') {
                        this._toggleRow($ev.data.record.id);
                        return;
                    }
                }

                // Call to server
                rpc.query({
                    model: $ev.data.record.model,
                    method: $ev.data.attrs.name,
                    args: [
                       [$ev.data.record.res_id]
                    ]
                }).then(function(res){
                    self._renderRowOfLines($ev.data.record.id, res);
                });
            } else {
                this._callButtonAction($ev.data.attrs, $ev.data.record);
            }
        }
    });
});
