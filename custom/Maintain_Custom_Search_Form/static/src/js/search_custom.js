odoo.define('Maintain.AdvancedSearch', function (require) {
"use strict";

    var core = require('web.core');
    var datepicker = require('web.datepicker');
    var field_utils = require('web.field_utils');
    var search_filters_registry = require('web.search_filters_registry_free');
    var Widget = require('web.Widget');

    var config = require('web.config');
    var core = require('web.core');
    var Domain = require('web.Domain');
    var DropdownMenu = require('web.DropdownMenu');
    var search_filters = require('web.search_filters_custom');

    var _t = core._t;
    var _lt = core._lt;

    var FilterMenu = require('web.FilterMenu_free');
    var QWeb = core.qweb;
    var model = null;
    var viewName = null;
    window.global_Filters = [];

    var My_FilterMenu = FilterMenu.include({
        /**
         * Init
         */
        init: function (a) {
            this._super.apply(this, arguments);

            if (a.action.res_model !== undefined) {
                model = a.action.res_model;
            } else if (a.action.controlPanelFieldsView !== undefined) {
                model = a.action.controlPanelFieldsView.model;
            }

            if (a.action.view_id) {
                viewName = a.action.view_id[1];
            } else if (a.action.controlPanelFieldsView !== undefined) {
                viewName = a.action.controlPanelFieldsView.name;
            }

            // Set alias
            var alias = this.alias || {};

            if (alias.model) {
                model = alias.model[model] || model;
            }

            if (alias.view) {
                viewName = alias.view[viewName] || viewName;
            }
        },

        /**
         * Operators for search
         */
        _operations: {
            'eq': {value: '='},
            'lt': {value: '<'},
            'lte': {value: '<='},
            'gt': {value: '>'},
            'gte': {value: '>='}
        },

        /**
         * Is advanced search model
         */
        _getAdvancedSearch: function(){
            if (!model || !this.advancedSearch || !this.advancedSearch[model]) {
                return;
            }

            if (viewName) {
                if (this.advancedSearch[model][viewName]) {
                    return this.advancedSearch[model][viewName];
                }
            }

            if (this.advancedSearch[model].template) {
                return this.advancedSearch[model];
            }

            return;
        },

        /**
         * Append proposition with template
         */
        _appendPropositionWithTemplate: function(){
            var mdl = 'm_' + model.replace('.', '__') + (viewName ? 'v_' + viewName.replace('.', '__') : '');
            this.$menu.find('>*:not(.o_add_filter_menu,.advanced_search_'+mdl+')').remove();
            if (this.$menu.find('.advanced_search_' + mdl).length == 0) {
                var setting = this._getAdvancedSearch();

                if (!setting){
                    return;
                }

                var html = QWeb.render(setting.template, {
                    records: this.advancedSearch[model].records || [],
                    res: this,
                    _t: _t,
                    _lt: _lt
                });

                this.$menu.prepend('<div class="advanced_search_'+mdl+' advanced_search">' + html + '</div>');
                var operations = this._operations;
                this.$menu.find('.filter-item').map(function(){
                    var item = $(this);
                    window.global_Filters.forEach(function (quotationsArray) {
                        var data_name = item.attr('data-name');
                        var data_operator = item.attr('data-operator');
                        if (operations[data_operator] !== undefined) {
                            data_operator = operations[data_operator].value;
                        }
                        if (quotationsArray[0] && data_name === quotationsArray[0] && data_operator === quotationsArray[1]) {
                            item.val(quotationsArray[2]);
                        }
                    });
                });
                //TH - done
            }
        },

        /**
         * Append proposition without template
         */
        _appendPropositionWithoutTemplate: function(){
            // make modern sear_filters code!!! It works but...
            var lV=[];
            var list_td = $('.o_list_table thead tr th');

            if(list_td){
                for(var i = 0; i < list_td.length; i++){
                    if($($('.o_list_table thead tr th')[i]).attr('data-name')){
                        lV.push($($('.o_list_table thead tr th')[i]).attr('data-name'));
                    }
                }
            }

            for (var key in this.fields) {
                var field =  this.fields[key]
                var hasHeader = lV.includes(key)?true:false;
                if (lV.length==0){
                    hasHeader = true;
                }
                if(field.searchable){
                    if( typeof this.__parentedParent !== 'undefined'){
                        if( typeof this.__parentedParent.searchBar !== 'undefined'){
                            if( typeof this.__parentedParent.searchBar.filterFields !== 'undefined'){
                                var listF = this.__parentedParent.searchBar.filterFields;
                                for(var i = 0; i<listF.length; i++){
                                    if((key === listF[i].attrs['name'] || field.type==='datetime')){
                                        if (lV.length>0 && hasHeader){
                                            var prop = new search_filters.ExtendedSearchProposition(this, this.fields);
                                            this.propositions.push(prop);
                                            this.$('.o_apply_filter').prop('disabled', false);
                                            prop.insertBefore(this.$addFilterMenu);
                                            for (var i =0; i< prop.attrs.fields.length; i++) {
                                                if(prop.attrs.fields[i].name === key){
                                                    prop.attrs.selected = prop.attrs.fields[i]
                                                }
                                            }

                                        }

                                    }
                                }
                            }
                        }
                    }
                }
            }
        },

        /**
         * Add a proposition inside the custom filter edition menu.
         *
         * @private
         * @returns {Promise}
         */
        _appendProposition: function () {
            if (this._getAdvancedSearch()) {
                this._appendPropositionWithTemplate();
            } else {
                this._appendPropositionWithoutTemplate();
			}
        },

        /**
         * Commit search with template
         */
        _commitSearchWithTemplate: function(){
            var _description = _t('Advanced search');
            if(typeof this.__parentedParent !== 'undefined'){
                 if(typeof this.__parentedParent.context !== 'undefined'){
                    if(typeof this.__parentedParent.context.lang !== 'undefined'){
                        if(this.__parentedParent.context.lang ==='en_US'){
                            _description = _t('Advanced search');
                        }else{
                            _description = _t('高度な検索');
                        }
                    }
                 }
            }

            var filters = [];
            var operations = this._operations;
            this.$menu.find('.filter-item').map(function(){
                var item = $(this);
                var val = item.val();

                if (val !== '') {
                    var op = item.attr('data-operator');

                    if (operations[op] !== undefined) {
                        op = operations[op].value;
                    }

                    filters.push([item.attr('data-name'), op, val]);
                }
            });

            if(filters.length > 0){
                this.trigger_up('new_filters', {filters: [{
                    type: 'filter',
                    description: _description,
                    subtype: 'filter1',
                    context: {'have_advance_search': true},
                    domain: JSON.stringify(filters),
                }]});
            }
            window.global_Filters = filters;
        },

        /**
         * Commit search without template
         */
        _commitSearchWithoutTemplate: function(){
            var self = this;
            var _description = _t('Advanced search');
            if(typeof this.__parentedParent !== 'undefined'){
                 if(typeof this.__parentedParent.context !== 'undefined'){
                    if(typeof this.__parentedParent.context.lang !== 'undefined'){
                        if(this.__parentedParent.context.lang ==='en_US'){
                            _description = _t('Advanced search');
                        }else{
                            _description = _t('高度な検索');
                        }
                    }
                 }
            }
            var filters = _.invoke(this.propositions, 'get_filter').map(function (preFilter) {
                return {
                    type: 'filter',
                    description: _description,
                    subtype: 'filter1',
                    domain: Domain.prototype.arrayToString(preFilter.attrs.domain),
                };
            });
            var domain = '[';
            if(filters.length>0){
                for(var i = 0; i<filters.length-1; i++){
                    var domain_other = filters[i].domain.substring(1, filters[i].domain.length-1);
                    var value =   domain_other.split('","');
                    if(value.length == 5  || value.length==3 ){
                        if(value.length==3){
                            if(!value.includes('"]') && !value.includes('None]') && typeof value !== 'undefined' && !value.includes('Invalid date"]') &&  value!='False]'){
                                    if(domain==='['){
                                        domain += domain_other;
                                    }else{
                                        domain += ',' + domain_other;
                                    }

                            }
                        }
                        else{
                            var tempV = value[2].split('],[');
                            var value1= [value[0],value[1],tempV[0]+']'];
                            if(!value1.includes('"]') && !value1.includes('None]') && typeof value1 !== 'undefined' && !value1.includes('Invalid date"]') &&  value1!='False]'){


                                    if(domain==='['){
                                        domain += value1[0] + '","' + value1[1] + '","' + value1[2];
                                    }else{
                                        domain += ',' + value1[0] + '","' + value1[1] + '","' + value1[2];
                                    }

                            }
                            var value2= ['['+tempV[1],value[3],value[4]];
                            if(!value2.includes('"]') && !value2.includes('None]') && typeof value2 !== 'undefined' && !value2.includes('Invalid date"]') && value2!='False]'){

                                    if(domain==='['){
                                        domain += value2[0] + '","' + value2[1] + '","' + value2[2];
                                    }else{
                                        domain += ',' + value2[0] + '","' + value2[1] + '","' + value2[2];
                                    }

                            }

                        }
//                      else{
//                            var value1= [value[0],value[1],value[2]]
//                            if(!value1.includes('""]') && !value1.includes('None]') && typeof value1 !== 'undefined' && !value1.includes('"Invalid date"]') &&  value1!='False]'){
//
//
//                                    if(domain==='['){
//                                        domain += value1[0] + '","' + value1[1] + '","' value1[2];
//                                    }else{
//                                        domain += ',' + value1[0] + '","' + value1[1] + '","' value1[2];
//                                    }
//
//                            }
//                            var value2= [value[3],value[4],value[5]];
//                            if(!value2.includes('""]') && !value2.includes('None]') && typeof value2 !== 'undefined' && !value2.includes('"Invalid date"]') && value2!='False]'){
//
//
//                                    if(domain==='['){
//                                        domain += value2[0] + '","' + value2[1] + '","' value2[2];
//                                    }else{
//                                        domain += ',' + value2[0] + '","' + value2[1] + '","' value2[2];
//                                    }
//
//                            }
//                        }





                    }

                }
            }
            domain += ']';
            if(filters.length>0){
                filters[0].domain = domain;
                 filters = filters.splice(0,1);
                 this.trigger_up('new_filters', {filters: filters});
            }
        },

        /**
         * When click on Apply button
         * Get all data in form search
         */
        _commitSearch: function () {
            if (this._getAdvancedSearch()) {
                this._commitSearchWithTemplate();
            } else {
                this._commitSearchWithoutTemplate();
            }
        },
    });
});
