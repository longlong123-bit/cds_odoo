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
        _renderLines: function($target, data){
            var $table = null;

            if (data.template) {
                $table = QWeb.render(data.template, {records: data.records});
            } else {
                // Table of line
                $table = $('<table></table');
                var $tbody = $('<tbody></tbody>');
                var $thead = $('<thead></thead>');
                var $trHead = $('<tr></tr>');
                $thead.append($trHead);
                $table.attr({
                    'class': 'table-lines'
                });

                // Get keys and generate header
                var headers = Object.keys(data[0]);

                for (var i = 0; i < headers.length; i++) {
                    $trHead.append('<th>' + headers[i] + '</th>');
                }

                // Add line to table of line
                for (var i = 0; i < data.length; i++) {
                    var $ltr = $('<tr></tr>');

                    for (var j = 0; j < headers.length; j++) {
                        if (data[i][headers[j]] !== undefined) {
                            $ltr.append('<td>' + data[i][headers[j]] + '</td>');
                        }
                    }

                    $tbody.append($ltr);
                }

                // Add table of line to row
                $table.append($thead);
                $table.append($tbody);
            }

            $target.append($table);
        },

        /**
         * Render lines
         */
        _renderRowOfLines: function(id, data){
            var $target = $('tr[data-id="'+id+'"]');
            // Create new row
            var $tr = $('<tr></tr>');
            $tr.attr({
                'data-ref': $target.attr('data-id'),
                'class': 'row-lines',
                'style': 'display: none'
            });

            if (data.records.length > 0) {
                $tr.append('<td></td>');

                // Create column contains table lines
                var $td = $('<td></td>');
                var $divTag = $('<div></div>');
                $divTag.addClass('table-responsive');
                $td.append($divTag);
                $td.attr({
                    colspan: $target.find('td').length - 1
                });
                $tr.append($td);

                this._renderLines($divTag, data);

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
            if ($ev.data.attrs.class === 'o_button_line') {
                // Check if row is exists
                var checkRow = $('tr.row-lines[data-ref="'+$ev.data.record.id+'"]');
                var self = this;

                if (checkRow.length > 0) {
                    this._toggleRow($ev.data.record.id);
                    return;
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
            }
        }
    });
});
