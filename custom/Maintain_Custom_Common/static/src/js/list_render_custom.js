odoo.define('web.ListRender_Custom', function (require) {
"use strict";
    // Allowed decoration on the list's rows: bold, italic and bootstrap semantics classes
    var DECORATIONS = [
        'decoration-bf',
        'decoration-it',
        'decoration-danger',
        'decoration-info',
        'decoration-muted',
        'decoration-primary',
        'decoration-success',
        'decoration-warning'
    ];

    var FIELD_CLASSES = {
        char: 'o_list_char',
        float: 'o_list_number',
        integer: 'o_list_number',
        monetary: 'o_list_number',
        text: 'o_list_text',
        many2one: 'o_list_many2one',
    };
    var BasicRenderer = require('web.BasicRenderer');
    var config = require('web.config');
    var core = require('web.core');
    var dom = require('web.dom');
    var field_utils = require('web.field_utils');
    var Pager = require('web.Pager');
    var utils = require('web.utils');
    var viewUtils = require('web.viewUtils');

    var EditableListRenderer = require('web.EditableListRenderer');

    var _t = core._t;

    var ListRender = require('web.ListRenderer');

    var My_ListRender = ListRender.include({
        events: _.extend({}, ListRender.prototype.events, {
            // event for 2 line invoice
            'click tbody tr td pre.o_data_cell': '_onCellClick',
            'click tbody tr td div.o_data_cell': '_onCellClick',
            'click thead tr th div.o_column_sortable': '_onSortColumn',
            'keydown tbody .o_data_cell': '_show_history_detail',
            'click .o_field_x2many_list_row_delete_m': 'onRemoveMultiClick'
        }),
        init: function () {
            this._super.apply(this, arguments);

        },
        /**
         * Render the main body of the table, with all its content.  Note that it
         * has been decided to always render at least 4 rows, even if we have less
         * data.  The reason is that lists with 0 or 1 lines don't really look like
         * a table.
         *
         * @private
         * @returns {jQueryElement} a jquery element <tbody>
         */
        _renderBody: function () {
            var self = this;
            var $rows = this._renderRows();
            while ($rows.length < 4) {
                $rows.push(self._renderEmptyRow());
            }
            window.current_data = this.state.data;
            return $('<tbody>').append($rows);
        },
        _show_history_detail: function(){
            if (event.code == 'KeyS' && event.ctrlKey && event.shiftKey) {
                $('.open_with_sort_cut').click();
            }
        },

        // Add custom
        /**
         * Event when click on first
         * Custom for 2line invoice
         */
        _renderRow_custom: function (record) {
            var self = this;
            if(self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view')){
                var $cells1 = this.columns.map(function (node, index) {
                    return self._renderBodyCell_custom(record, node, index, { mode: 'readonly' });
                });

                var $td_0 =  $('<td>').append($cells1[1]);
                    $td_0.append($cells1[2]);
                var $td_1 =  $('<td>').append($cells1[3]);
                    $td_1.append($cells1[4]);
                var $td_2 =  $('<td>').append($cells1[5]);
                    $td_2.append($cells1[6]);

                var $td_3 =  $('<td>').append($cells1[7]);
                var $td_4 =  $('<td>').append($cells1[8]);
                var $td_5 =  $('<td>').append($cells1[9]);
                var $td_6 =  $('<td>').append($cells1[10]);
                var $td_7 =  $('<td>').append($cells1[11]);
                var $td_8 =  $('<td>').append($cells1[12]);

                var $td_9 =  $('<td>').append($cells1[13]);
                var $td_10 =  $('<td>').append($cells1[14]);
                $td_10.append($cells1[15]);
                var $td_11 =  $('<td>').append($cells1[16]);
                $td_11.append($cells1[17]);
                var $tr = $('<tr>', { class: 'o_data_row' })
                    .attr('data-id', record.id)
                    .append($td_0)
                    .append($td_1)
                    .append($td_2)
                    .append($td_3)
                    .append($td_4)
                    .append($td_5)
                    .append($td_6)
                    .append($td_7)
                    .append($td_8)
                    .append($td_9)
                    .append($td_10)
                    .append($td_11);
                if(this.editable){
                    $tr.prepend(this._renderSelector('td'));
                }
                return $tr;
            }else{
                var $cells = this.columns.map(function (node, index) {
                    return self._renderBodyCell(record, node, index, { mode: 'readonly' });
                });

                var $tr = $('<tr/>', { class: 'o_data_row' })
                    .attr('data-id', record.id)
                    .append($cells);
                if (this.hasSelectors) {
                    $tr.prepend(this._renderSelector('td', !record.res_id));
                }
                this._setDecorationClasses(record, $tr);
                return $tr;
            }
        },

        _renderSelector_radio: function (tag, disableInput) {
        var $content = dom.renderCheckbox();
        if (disableInput) {
            $content.find("input[type='checkbox']").prop('disabled', disableInput);
        }
        return $('<' + tag + '>')
            .addClass('o_list_record_selector')
            .append($content);
    },

        // Add custom
        /**
         *
         * Custom for 2line invoice
         */
        _renderHeaderCell_custom: function (node) {
            var self = this;
            const { icon, name, string } = node.attrs;
            var order = this.state.orderedBy;
            var isNodeSorted = order[0] && order[0].name === name;
            var field = this.state.fields[name];
            var $thWrap =$('<th>');
            var $th = $('<div>');
            if (name) {
                $th.attr('data-name', name);
            } else if (string) {
                $th.attr('data-string', string);
            } else if (icon) {
                $th.attr('data-icon', icon);
            }
            if (node.attrs.editOnly) {

                $th.addClass('oe_edit_only');
            }
            if (node.attrs.readOnly) {
                $th.addClass('oe_read_only');
            }
            if (!field) {
                return $th;
            }
            var description = string || field.string;
            if (node.attrs.widget) {
                $th.addClass(' o_' + node.attrs.widget + '_cell');
                if (this.state.fieldsInfo.list[name].Widget.prototype.noLabel) {
                    description = '';
                }
            }
            $th.text(description)
                .attr('tabindex', -1)
                .toggleClass('o-sort-down', isNodeSorted ? !order[0].asc : false)
                .toggleClass('o-sort-up', isNodeSorted ? order[0].asc : false)
                .addClass(field.sortable && 'o_column_sortable');

            if (isNodeSorted) {
                $th.attr('aria-sort', order[0].asc ? 'ascending' : 'descending');
            }

            if (field.type === 'float' || field.type === 'integer' || field.type === 'monetary') {
                $th.addClass('o_list_number_th');
            }

            if (config.isDebug()) {
                var fieldDescr = {
                    field: field,
                    name: name,
                    string: description || name,
                    record: this.state,
                    attrs: _.extend({}, node.attrs, this.state.fieldsInfo.list[name]),
                };
                this._addFieldTooltip(fieldDescr, $th);
            } else {
                $th.attr('title', description);
            }
            return $th;
        },

        // Override
        /**
         *
         * Render Header Cell
         */
        _renderHeaderCell: function(node) {
            const {icon, name, string} = node.attrs;
            var order = this.state.orderedBy;
            var isNodeSorted = order[0] && order[0].name === name;
            var field = this.state.fields[name];
            var $th = $('<th>');

            // Check hide column with attribute issue_format
            if (node.attrs.modifiers &&
                    node.attrs.modifiers.issue_format) {
                var attr_issue_format = node.attrs.modifiers.issue_format;
                if (this.state.domain.length <= 0) {
                    if (attr_issue_format != '0') {
                        this.columns = this.columns.filter(function(val) {
                            return val.attrs.name != name;
                        });
                        return '';
                    }
                } else {
                    var array_issue_format = this.state.domain.filter(function(val) {
                        return val[0] == 'issue_format';
                    });
                    var input_issue_format = array_issue_format[0][2];
                    if (attr_issue_format != input_issue_format) {
                        this.columns = this.columns.filter(function(val) {
                            return val.attrs.name != name;
                        });
                        return '';
                    }
                }
            }

            if (name) {
                $th.attr('data-name', name);
            } else if (string) {
                $th.attr('data-string', string);
            } else if (icon) {
                $th.attr('data-icon', icon);
            }
            if (node.attrs.editOnly) {
                $th.addClass('oe_edit_only');
            }
            if (node.attrs.readOnly) {
                $th.addClass('oe_read_only');
            }
            if (!field) {
                return $th;
            }
            var description = string || field.string;
            if (node.attrs.widget) {
                $th.addClass(' o_' + node.attrs.widget + '_cell');
                if (this.state.fieldsInfo.list[name].Widget.prototype.noLabel) {
                    description = '';
                }
            }
            $th.text(description).attr('tabindex', -1).toggleClass('o-sort-down', isNodeSorted ? !order[0].asc : false).toggleClass('o-sort-up', isNodeSorted ? order[0].asc : false).addClass(field.sortable && 'o_column_sortable');
            if (isNodeSorted) {
                $th.attr('aria-sort', order[0].asc ? 'ascending' : 'descending');
            }
            if (field.type === 'float' || field.type === 'integer' || field.type === 'monetary') {
                $th.addClass('o_list_number_th');
            }
            if (config.isDebug()) {
                var fieldDescr = {
                    field: field,
                    name: name,
                    string: description || name,
                    record: this.state,
                    attrs: _.extend({}, node.attrs, this.state.fieldsInfo.list[name]),
                };
                this._addFieldTooltip(fieldDescr, $th);
            } else {
                $th.attr('title', description);
            }
            return $th;
        },

        // Add custom
        /**
         *
         * Custom for 2line invoice
         */
        _renderBodyCell_custom: function (record, node, colIndex, options) {
            var self = this;
            var tdClassName = 'o_data_cell';
            if(node.attrs.name!='sequence'){
                if (node.tag === 'button') {
                    tdClassName += ' o_list_button';
                } else if (node.tag === 'field') {
                        tdClassName += ' o_field_cell';
                        var typeClass = FIELD_CLASSES[this.state.fields[node.attrs.name].type];
                        if (typeClass) {
                            tdClassName += (' ' + typeClass);
                        }
                        if (node.attrs.widget) {
                            tdClassName += (' o_' + node.attrs.widget + '_cell');
                        }
                }
                if (node.attrs.editOnly) {
                    tdClassName += ' oe_edit_only';
                }
                if (node.attrs.readOnly) {
                    tdClassName += ' oe_read_only';
                }
                if (record.fields[node.attrs.name] && record.fields[node.attrs.name].type == 'text'){
                    var $td = $('<pre>', { class: tdClassName, tabindex: -1 });
                } else {
                    var $td = $('<div>', { class: tdClassName, tabindex: -1 });
                }


                // We register modifiers on the <td> element so that it gets the correct
                // modifiers classes (for styling)
                var modifiers = this._registerModifiers(node, record, $td, _.pick(options, 'mode'));
                // If the invisible modifiers is true, the <td> element is left empty.
                // Indeed, if the modifiers was to change the whole cell would be
                // rerendered anyway.
                if (modifiers.invisible && !(options && options.renderInvisible)) {
                    return $td;
                }

                if (node.tag === 'button') {
                    if(node.attrs.name==='button_update' && this.editable){
                        return $td.append(this._renderButton(record, node));
                    }else{
                        return $td.append('');
                    }
                } else if (node.tag === 'widget') {
                    return $td.append(this._renderWidget(record, node));
                }
                if (node.attrs.widget || (options && options.renderWidgets)) {
                    var $el = this._renderFieldWidget(node, record, _.pick(options, 'mode'));
                    return $td.append($el);
                }
                this._handleAttributes($td, node);
                var name = node.attrs.name;
                var field = this.state.fields[name];
                var value = record.data[name];
                var formatter = field_utils.format[field.type];
                var formatOptions = {
                    escape: true,
                    data: record.data,
                    isPassword: 'password' in node.attrs,
                    digits: node.attrs.digits && JSON.parse(node.attrs.digits),
                };
                var formattedValue = formatter(value, field, formatOptions);
                var title = '';
                if (field.type !== 'boolean') {
                    title = formatter(value, field, _.extend(formatOptions, {escape: false}));
                }
                return $td.html(formattedValue).attr('title', title);
            }
        },

        // Override
        /**
         *
         * Custom for 2line invoice
         */
        _onCellClick: function (event) {
            // The special_click property explicitely allow events to bubble all
            // the way up to bootstrap's level rather than being stopped earlier.
            var $td = $(event.currentTarget);
            if(this.$el.hasClass('invoice_create o_list_view') || this.$el.hasClass('quotations_custom_details o_list_view')){
                var $tr = $td.parent().parent();
            }else{
                var $tr = $td.parent();
            }
            var rowIndex = $tr.prop('rowIndex') - 1;
            if (!this._isRecordEditable($tr.data('id')) || $(event.target).prop('special_click')) {
                return;
            }
            var fieldIndex = Math.max($tr.find('.o_field_cell').index($td), 0);
            this._selectCell(rowIndex, fieldIndex, {event: event});
        },

        // Override
        /**
         *
         * Custom for 2line invoice
         */
        _renderHeader: function () {
            var HEADER1 = [
                'button_update',
                'invoice_custom_line_no',
                'product_code',
                'product_maker_name',
                'product_name',
                'invoice_custom_standardnumber',
                'quantity',
                'price_unit',
                'product_uom_id',
                'invoice_custom_lineamount',
                'product_standard_price',
                'invoice_custom_Description',
               ];
            var HEADER2 = [
               'x_invoicelinetype',
               'product_barcode',
               'x_product_cost_price',
               'tax_rate',
            ];
            if(this.$el.hasClass('quotations_custom_details o_list_view')){
                HEADER1 = [
                    'button_update',
                    'quotation_custom_line_no',
                    'product_code',
                    'product_maker_name',
                    'product_name',
                    'product_standard_number',
                    'product_uom_qty',
                    'price_unit',
                    'product_uom_id',
                    'line_amount',
                    'product_standard_price',
                    'description',
                   ];
                HEADER2 = [
                   'class_item',
                   'product_barcode',
                   'cost',
                   'tax_rate',
                ];
            }
            var headerCol1 = [];
            var headerCol2 = [];
            var totalHeader = 0;

            if(this.columns && this.columns.length>0){
                for(var i=0; i<this.columns.length;i++){
                    if(HEADER1.includes(this.columns[i].attrs.name)){
                        headerCol1.push(this.columns[i]);
                        totalHeader++;
                    }else if(HEADER2.includes(this.columns[i].attrs.name)){
                        headerCol2.push(this.columns[i]);
                        totalHeader++;
                    }
                }
            }
            if(totalHeader == HEADER1.length+ HEADER2.length){
                var $tr1 = _.map(headerCol1, this._renderHeaderCell_custom.bind(this));
                var $tr2 = _.map(headerCol2, this._renderHeaderCell_custom.bind(this));
                var $hr =  '<hr style="margin-top: 0rem; margin-bottom: 0rem; margin-left:-20px; margin-right:-20px"/>';
                var $tr_th= $('<tr>');
                var $tr_header =$('<th>')
                for(var i =0; i<$tr1.length;i++){
                    if(i==1 || i==2){
                        $tr_header = $('<th>').append($tr1[i])
                            .append($hr)
                            .append($tr2[i-1]);
                    }else if (i==10 || i==11){
                        $tr_header = $('<th>').append($tr1[i])
                            .append($hr)
                            .append($tr2[i-8]);
                    } else {
                        $tr_header = $('<th>').append($tr1[i]);
                    }

                    if ($tr_header[0].innerHTML.length && this._hasVisibleRecords(this.state)) {
                        const resizeHandle = document.createElement('span');
                        resizeHandle.classList = 'o_resize';
                        resizeHandle.onclick = this._onClickResize.bind(this);
                        resizeHandle.onmousedown = this._onStartResize.bind(this);
                        $tr_header.append(resizeHandle);
                    }
                    $tr_th.append($tr_header);
                }
                if (this.editable){
                    $tr_th.prepend(this._renderSelector('th'));
                }
                $tr_th.append($('<th>'));
                var $tr = $('<thead>').append($tr_th);
                return $tr;
            }

            var $tr = $('<tr>').append(_.map(this.columns, this._renderHeaderCell.bind(this)));

            if (this.hasSelectors) {
                $tr.prepend(this._renderSelector('th'));
            }

            return $('<thead>').append($tr);

        },

        // Override
        /**
         *
         * Custom for 2line invoice
         */
        _renderRow: function (record, index) {
            var self = this;

            if(this.$el.hasClass('invoice_create o_list_view') || this.$el.hasClass('quotations_custom_details o_list_view')){
                if(this.editable){
                    this.addTrashIcon = true;
                }else{
                    this.addTrashIcon = false;
                }

            }
            var $row = self._renderRow_custom(record);
            if (this.addTrashIcon) {
                var $icon = this.isMany2Many ?
                    $('<button>', {'class': 'fa fa-times', 'name': 'unlink', 'aria-label': _t('Unlink row ') + (index + 1)}) :
                    $('<button>', {'class': 'fa fa-trash-o', 'name': 'delete', 'aria-label': _t('Delete row ') + (index + 1)});
                var $td = $('<td>', {class: 'o_list_record_remove'}).append($icon);
                $row.append($td);
            }
            return $row;
        },

        _renderFooter: function () {
            var aggregates = {};
             if(!this.$el.hasClass('invoice_create o_list_view') && !this.$el.hasClass('quotations_custom_details o_list_view')){
            _.each(this.columns, function (column) {
                if ('aggregate' in column) {
                    aggregates[column.attrs.name] = column.aggregate;
                }
            });
            var $cells = this._renderAggregateCells(aggregates);
            if (this.hasSelectors) {
                $cells.unshift($('<td>'));
            }
            return $('<tfoot>').append($('<tr>').append($cells));
            }else{
                var $tr=$('<tr>')
                var lengthFooter = this.editable?10:9;
                for(var i =0; i<lengthFooter; i++){
                    $tr.append($('<td>'));
                }
                return $('<tfoot>').append($tr);
            }
        },

        /**
         * Gets the th element corresponding to a given column.
         *
         * @private
         * @param {Object} column
         * @returns {HTMLElement}
         */
        _getColumnHeader: function (column) {
            var self = this;
            const { icon, name, string } = column.attrs;
            if(self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view')){
                if (name) {
                    return this.el.querySelector(`thead th div[data-name="${name}"]`);
                } else if (string) {
                    return this.el.querySelector(`thead th div[data-string="${string}"]`);
                } else if (icon) {
                    return this.el.querySelector(`thead th div[data-icon="${icon}"]`);
                }
             }else{
                if (name) {
                    return this.el.querySelector(`thead th[data-name="${name}"]`);
                } else if (string) {
                    return this.el.querySelector(`thead th[data-string="${string}"]`);
                } else if (icon) {
                    return this.el.querySelector(`thead th[data-icon="${icon}"]`);
                }
             }
        },


        /**
         * Render a single <th> with the informations for a column. If it is not a
         * field, the th will be empty. Otherwise, it will contains all relevant
         * information for the field.
         *
         * @private
         * @param {Object} node
         * @returns {jQueryElement} a <th> element
         */
        setRowMode: function (recordID, mode) {
            var self = this;
            var record = self._getRecord(recordID);
            if (!record) {
                return Promise.resolve();
            }

            var editMode = (mode === 'edit');
            var $row = this._getRow(recordID);
            this.currentRow = editMode ? $row.prop('rowIndex') - 1 : null;
            //var $tds = $row.children.c('.o_data_cell');
            if(self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view')){
                var $tds = $row.children().children();
            }else{
                var $tds = $row.children('.o_data_cell');
            }
            var oldWidgets = _.clone(this.allFieldWidgets[record.id]);

            // Prepare options for cell rendering (this depends on the mode)
            var options = {
                renderInvisible: editMode,
                renderWidgets: editMode,
            };
            options.mode = editMode ? 'edit' : 'readonly';

            // Switch each cell to the new mode; note: the '_renderBodyCell'
            // function might fill the 'this.defs' variables with multiple promise
            // so we create the array and delete it after the rendering.
            var defs = [];
            this.defs = defs;
            _.each(this.columns, function (node, colIndex) {
                var $td = $tds.eq(colIndex);
                if(self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view')){
                    var $newTd = self._renderBodyCell_custom(record, node, colIndex, options);
                }else{
                    var $newTd = self._renderBodyCell(record, node, colIndex, options);
                }

                // Widgets are unregistered of modifiers data when they are
                // destroyed. This is not the case for simple buttons so we have to
                // do it here.
                if ($td.hasClass('o_list_button')) {
                    self._unregisterModifiersElement(node, recordID, $td.children());
                }

                // For edit mode we only replace the content of the cell with its
                // new content (invisible fields, editable fields, ...).
                // For readonly mode, we replace the whole cell so that the
                // dimensions of the cell are not forced anymore.
                if (editMode) {
                    if($td.hasClass('custom-control custom-checkbox') &&
                    (self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view'))){
                        // do nothing
                    }else{
                        $td.empty().append($newTd.contents());
                    }

                } else {
                    self._unregisterModifiersElement(node, recordID, $td);
                    if($td.hasClass('custom-control custom-checkbox') &&
                    (self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view'))){
                        //do nothing
                    } else{
                        $td.replaceWith($newTd);
                    }

                }
            });
            delete this.defs;

            // Destroy old field widgets
            _.each(oldWidgets, this._destroyFieldWidget.bind(this, recordID));

            // Toggle selected class here so that style is applied at the end
            $row.toggleClass('o_selected_row', editMode);
            if (editMode) {
                this._disableRecordSelectors();
            } else {
                this._enableRecordSelectors();
            }

            return Promise.all(defs).then(function () {
                // necessary to trigger resize on fieldtexts
                core.bus.trigger('DOM_updated');
            });
        },

        /**
         * Gets the th element corresponding to a given column.
         *
         * @private
         * @param {Object} column
         * @returns {HTMLElement}
         */
        _getColumnHeader: function (column) {
            var self = this;
            const { icon, name, string } = column.attrs;
            if(self.$el.hasClass('invoice_create o_list_view') || self.$el.hasClass('quotations_custom_details o_list_view')){
                if (name) {
                    return this.el.querySelector(`thead th div[data-name="${name}"]`);
                } else if (string) {
                    return this.el.querySelector(`thead th div[data-string="${string}"]`);
                } else if (icon) {
                    return this.el.querySelector(`thead th div[data-icon="${icon}"]`);
                }
             }else{
                if (name) {
                    return this.el.querySelector(`thead th[data-name="${name}"]`);
                } else if (string) {
                    return this.el.querySelector(`thead th[data-string="${string}"]`);
                } else if (icon) {
                    return this.el.querySelector(`thead th[data-icon="${icon}"]`);
                }
             }
        },

        /**
         * Handles the assignation of default widths for each column header.
         * If the list is empty, an arbitrary absolute or relative width will be
         * given to the header
         *
         * @see _getColumnWidth for detailed information about which width is
         * given to a certain field type.
         *
         * @private
         */
        _computeDefaultWidths: function () {
            const isListEmpty = !this._hasVisibleRecords(this.state);
            const relativeWidths = [];
            this.columns.forEach(column => {
                const th = this._getColumnHeader(column);
                if(th!=null){
                    if (th.offsetParent === null) {
                        relativeWidths.push(false);
                    } else {
                        const width = this._getColumnWidth(column);
                        if (width.match(/[a-zA-Z]/)) { // absolute width with measure unit (e.g. 100px)
                            if (isListEmpty) {
                                th.style.width = width;
                            } else {
                                // If there are records, we force a min-width for fields with an absolute
                                // width to ensure a correct rendering in edition
                                th.style.minWidth = width;
                            }
                            relativeWidths.push(false);
                        } else { // relative width expressed as a weight (e.g. 1.5)
                            relativeWidths.push(parseFloat(width, 10));
                        }
                    }
                }
            });

            // Assignation of relative widths
            if (isListEmpty) {
                const totalWidth = this._getColumnsTotalWidth(relativeWidths);
                for (let i in this.columns) {
                    if (relativeWidths[i]) {
                        const th = this._getColumnHeader(this.columns[i]);
                         if(th!=null){
                            th.style.width = (relativeWidths[i] / totalWidth * 100) + '%';
                         }
                    }
                }
                // Manualy assigns trash icon header width since it's not in the columns
                const trashHeader = this.el.getElementsByClassName('o_list_record_remove_header')[0];
                if (trashHeader) {
                    trashHeader.style.width = '32px';
                }
            }
        },

        onRemoveMultiClick: function (event) {
            event.stopPropagation();
            if (this.confirmOnDelete) {
                Dialog.confirm(this, _t("Are you sure you want to delete this record ?"), {
                    confirm_callback: doIt,
                });
            } else {
               var self = this;
               for (var i = 0; i <self.selection.length ; i++ ){
                    self.trigger_up('list_record_remove', {id: self.selection[i]});
               }
            }

        },

        /**
     * Whenever we change the state of the selected rows, we need to call this
     * method to keep the this.selection variable in sync, and also to recompute
     * the aggregates.
     *
     * @private
     */
    _updateSelection: function () {

        this.selection = [];
        var self = this;
        var $inputs = this.$('tbody .o_list_record_selector input:visible:not(:disabled)');
        var allChecked = $inputs.length > 0;
        var hasChecked = false;
        $inputs.each(function (index, input) {
            if (input.checked) {
                self.selection.push($(input).closest('tr').data('id'));
                hasChecked = true;
            } else {
                allChecked = false;
            }
        });
        if(hasChecked === true){
            this.$el.find('.o_field_x2many_list_row_delete_m').show();
        }else{
            this.$el.find('.o_field_x2many_list_row_delete_m').hide();
        }
        this.$('thead .o_list_record_selector input').prop('checked', allChecked);
        this.trigger_up('selection_changed', { selection: this.selection });
        this._updateFooter();
        },

    /**
     * Handles the keyboard navigation according to events triggered by field
     * widgets.
     * - previous: move to the first activable cell on the left if any, if not
     *          move to the rightmost activable cell on the row above.
     * - next: move to the first activable cell on the right if any, if not move
     *          to the leftmost activable cell on the row below.
     * - next_line: move to leftmost activable cell on the row below.
     *
     * Note: moving to a line below if on the last line or moving to a line
     * above if on the first line automatically creates a new line.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onNavigationMove: function (ev) {
        var self = this;
        // Don't stop the propagation when navigating up while not editing any row
        if (this.currentRow === null && ev.data.direction === 'up') {
            return;
        }
        ev.stopPropagation(); // stop the event, the action is done by this renderer
        switch (ev.data.direction) {
            case 'previous':
                if (this.currentFieldIndex > 0) {
                    this._selectCell(this.currentRow, this.currentFieldIndex - 1, {inc: -1, wrap: false})
                        .guardedCatch(this._moveToPreviousLine.bind(this));
                } else {
                    this._moveToPreviousLine();
                }
                break;
            case 'next':
                if(this.$el.hasClass('quotations_custom_details') || this.$el.hasClass('invoice_create')){
                  var focus_index = [3,4,8,10,this.columns.length - 2];
                  var currentIndex = this.currentFieldIndex;
                  var index = focus_index.findIndex(function(number) {
                    return number > currentIndex;
                  });
                  this.currentFieldIndex = index > -1 ? focus_index[index] -1 : this.currentFieldIndex;
                }
                if (this.currentFieldIndex + 1 < this.columns.length) {
                    this._selectCell(this.currentRow, this.currentFieldIndex + 1, {wrap: false})
                        .guardedCatch(this._moveToNextLine.bind(this));
                } else {
                    this._moveToNextLine();
                }
                break;
            case 'next_line':
                // If the list is readonly and the current is the only record editable, we unselect the line
                if (!this.editable && this.selection.length === 1 &&
                    this._getRecordID(this.currentRow) === ev.target.dataPointID) {
                    this.unselectRow();
                } else {
                    this._moveToNextLine({ forceCreate: true });
                }
                break;
            case 'cancel':
                // stop the original event (typically an ESCAPE keydown), to
                // prevent from closing the potential dialog containing this list
                // also auto-focus the 1st control, if any.
                ev.data.originalEvent.stopPropagation();
                var rowIndex = this.currentRow;
                var cellIndex = this.currentFieldIndex + 1;
                this.trigger_up('discard_changes', {
                    recordID: ev.target.dataPointID,
                    onSuccess: function () {
                        self._enableRecordSelectors();
                        var recordId = self._getRecordID(rowIndex);
                        if (recordId) {
                            var correspondingRow = self._getRow(recordId);
                            correspondingRow.children().eq(cellIndex).focus();
                        } else if (self.currentGroupId) {
                            self.$('a[data-group-id="' + self.currentGroupId + '"]').focus();
                        } else {
                            self.$('.o_field_x2many_list_row_add a:first').focus(); // FIXME
                        }
                    }
                });
                break;
        }
    },
    /**
     * Moves the focus to the nearest editable row before or after the current one.
     * If we arrive at the end of the list (or of a group in the grouped case) and the list
     * is editable="bottom", we create a new record, otherwise, we move the
     * cursor to the first row (of the next group in the grouped case).
     *
     * @private
     * @param {number} next whether to move to the next or previous row
     * @param {Object} [options]
     * @param {boolean} [options.forceCreate=false] typically set to true when
     *   navigating with ENTER ; in this case, if the next row is the 'Add a
     *   row' one, always create a new record (never skip it, like TAB does
     *   under some conditions)
     */
    _moveToSideLine: function (next, options) {
        options = options || {};
        const recordID = this._getRecordID(this.currentRow);
        this.commitChanges(recordID).then(() => {
            const record = this._getRecord(recordID);
            const multiEdit = this.isInMultipleRecordEdition(recordID);
            if (!multiEdit) {
                const fieldNames = this.canBeSaved(recordID);
                if (fieldNames.length && (record.isDirty() || options.forceCreate)) {
                    // the current row is invalid, we only leave it if it is not dirty
                    // (we didn't make any change on this row, which is a new one) and
                    // we are navigating with TAB (forceCreate=false)
                    return;
                }
            }
            // compute the index of the next (record) row to select, if any
            const side = next ? 'first' : 'last';
            const borderRowIndex = this._getBorderRow(side).prop('rowIndex') - 1;
            var cellIndex = 0;
            if(this.$el.hasClass('quotations_custom_details') || this.$el.hasClass('invoice_create')){
              cellIndex = next ? 3 : this.allFieldWidgets[recordID].length - 1;
            } else {
              cellIndex = next ? 0 : this.allFieldWidgets[recordID].length - 1;
            }
            const cellOptions = { inc: next ? 1 : -1, force: true };
            const $currentRow = this._getRow(recordID);
            const $nextRow = this._getNearestEditableRow($currentRow, next);
            let nextRowIndex = null;
            let groupId;

            if (!this.isGrouped) {
                // ungrouped case
                if ($nextRow.length) {
                    nextRowIndex = $nextRow.prop('rowIndex') - 1;
                } else if (!this.editable) {
                    nextRowIndex = borderRowIndex;
                } else if (!options.forceCreate && !record.isDirty()) {
                    this.trigger_up('discard_changes', {
                        recordID: recordID,
                        onSuccess: this.trigger_up.bind(this, 'activate_next_widget', { side: side }),
                    });
                    return;
                }
            } else {
                // grouped case
                var $directNextRow = $currentRow.next();
                if (next && this.editable === "bottom" && $directNextRow.hasClass('o_add_record_row')) {
                    // the next row is the 'Add a line' row (i.e. the current one is the last record
                    // row of the group)
                    if (options.forceCreate || record.isDirty()) {
                        // if we modified the current record, add a row to create a new record
                        groupId = $directNextRow.data('group-id');
                    } else {
                        // if we didn't change anything to the current line (e.g. we pressed TAB on
                        // each cell without modifying/entering any data), we discard that line (if
                        // it was a new one) and move to the first record of the next group
                        nextRowIndex = ($nextRow.prop('rowIndex') - 1) || null;
                        this.trigger_up('discard_changes', {
                            recordID: recordID,
                            onSuccess: () => {
                                if (nextRowIndex !== null) {
                                    if (!record.res_id) {
                                        // the current record was a new one, so we decrement
                                        // nextRowIndex as that row has been removed meanwhile
                                        nextRowIndex--;
                                    }
                                    this._selectCell(nextRowIndex, cellIndex, cellOptions);
                                } else {
                                    // we were in the last group, so go back to the top
                                    this._selectCell(borderRowIndex, cellIndex, cellOptions);
                                }
                            },
                        });
                        return;
                    }
                } else {
                    // there is no 'Add a line' row (i.e. the create feature is disabled), or the
                    // list is editable="top", we focus the first record of the next group if any,
                    // or we go back to the top of the list
                    nextRowIndex = $nextRow.length ?
                        ($nextRow.prop('rowIndex') - 1) :
                        borderRowIndex;
                }
            }

            // if there is a (record) row to select, select it, otherwise, add a new record (in the
            // correct group, if the view is grouped)
            if (nextRowIndex !== null) {
                // cellOptions.force = true;
                this._selectCell(nextRowIndex, cellIndex, cellOptions);
            } else if (this.editable) {
                // if for some reason (e.g. create feature is disabled) we can't add a new
                // record, select the first record row
                this.unselectRow().then(this.trigger_up.bind(this, 'add_record', {
                    groupId: groupId,
                    onFail: this._selectCell.bind(this, borderRowIndex, cellIndex, cellOptions),
                }));
            }
        });
    },
    /**
     * Edit a given record in the list
     *
     * @param {string} recordID
     */
    editRecord: function (recordID) {
        var $row = this._getRow(recordID);
        var rowIndex = $row.prop('rowIndex') - 1;
        if(this.$el.hasClass('quotations_custom_details') || this.$el.hasClass('invoice_create')){
          this._selectCell(rowIndex, 3);
        } else {
          this._selectCell(rowIndex, 0);
        }
    },
    });
    ListRender.include(My_ListRender);
});
