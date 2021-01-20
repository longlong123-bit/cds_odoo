odoo.define('web.FormController.custom', function (require) {
"use strict";
    var s = require('web.ServiceProviderMixin');
    var AbstractController = require('web.AbstractController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var FieldManagerMixin = require('web.FieldManagerMixin');
    var Pager = require('web.Pager');
    var TranslationDialog = require('web.TranslationDialog');
    var ServicesMixin = require('web.ServicesMixin');
    var _t = core._t;
    var FormController = require('web.FormController');

    var My_FormController = FormController.include({
        init: function () {
            this._super.apply(this, arguments);
            this.handle = this.initialState.id;
        },

        _onSave: function (ev) {
            ev.stopPropagation(); // Prevent x2m lines to be auto-saved
            var self = this;
            this._disableButtons();
            this.saveRecord(self.handle, {stayInEdit: true, reload: true,}).then(this._enableButtons.bind(this)).then(function() {
                    $("#success-alert").fadeTo(3000, 500).slideUp(500, function() {
                      $("#success-alert").slideUp(500);
                    });
                }).guardedCatch(this._enableButtons.bind(this));
        },

        /*TH - custom when click save auto transfer to create form*/
        // saveRecord: function () {
        //     var self = this;
        //     return this._super.apply(this, arguments).then(function (changedFields) {
        //         // the title could have been changed
        //         self._setTitle(self.getTitle());
        //         self._updateEnv();
        //         if (_t.database.multi_lang && changedFields.length) {
        //             // need to make sure changed fields that should be translated
        //             // are displayed with an alert
        //             var fields = self.renderer.state.fields;
        //             var data = self.renderer.state.data;
        //             var alertFields = {};
        //             for (var k = 0; k < changedFields.length; k++) {
        //                 var field = fields[changedFields[k]];
        //                 var fieldData = data[changedFields[k]];
        //                 if (field.translate && fieldData) {
        //                     alertFields[changedFields[k]] = field;
        //                 }
        //             }
        //             if (!_.isEmpty(alertFields)) {
        //                 self.renderer.updateAlertFields(alertFields);
        //             }
        //             self.createRecord();
        //         }
        //         return changedFields;
        //     });
        // },
        /*TH - done*/

        _confirmSave: function (id) {
            if (id === this.handle) {
                return this.reload();
            } else {
                // A subrecord has changed, so update the corresponding relational field
                // i.e. the one whose value is a record with the given id or a list
                // having a record with the given id in its data
                var record = this.model.get(this.handle);

                // Callback function which returns true
                // if a value recursively contains a record with the given id.
                // This will be used to determine the list of fields to reload.
                var containsChangedRecord = function (value) {
                    return _.isObject(value) &&
                        (value.id === id || _.find(value.data, containsChangedRecord));
                };

                var changedFields = _.findKey(record.data, containsChangedRecord);
                return this.renderer.confirmChange(record, record.id, [changedFields]);
            }
        },

        _updateSidebar: function () {
        if (this.sidebar) {
            // this.sidebar.do_toggle(this.mode === 'readonly');
            // Hide/Show Archive/Unarchive dropdown items
            // We could have toggled the o_hidden class on the
            // item theirselves, but the items are redrawed
            // at each update, based on the initial definition
            var archive_item = _.find(this.sidebar.items.other, function(item) {
                return item.classname && item.classname.includes('o_sidebar_item_archive')
            })
            var unarchive_item = _.find(this.sidebar.items.other, function(item) {
                return item.classname && item.classname.includes('o_sidebar_item_unarchive')
            })
            if (archive_item && unarchive_item) {
                if (this.renderer.state.data.active) {
                    archive_item.classname = 'o_sidebar_item_archive';
                    unarchive_item.classname = 'o_sidebar_item_unarchive o_hidden';
                } else {
                    archive_item.classname = 'o_sidebar_item_archive o_hidden';
                    unarchive_item.classname = 'o_sidebar_item_unarchive';
                }
            }
        }
    },




    });
    FormController.include(FormController);
});