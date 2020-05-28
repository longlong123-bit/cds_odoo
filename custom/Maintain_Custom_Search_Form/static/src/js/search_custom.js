odoo.define('search.Custom', function (require) {
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
    var model = null;

    var My_FilterMenu = FilterMenu.include({
        events: _.extend({}, FilterMenu.prototype.events, {
        }),
        init: function (a) {
            this._super.apply(this, arguments);
            model = a.action.res_model;
        },

        /**
         * Add a proposition inside the custom filter edition menu.
         *
         * @private
         * @returns {Promise}
         */
        _appendProposition: function () {
            // make modern sear_filters code!!! It works but...
            var lV=[];

            if (window.advancedSearch && window.advancedSearch[model]) {
                lV = window.advancedSearch[model];
            } else {
                var list_td = $('.o_list_table thead tr th');

                if(list_td){
                    for(var i = 0; i < list_td.length; i++){
                        if($($('.o_list_table thead tr th')[i]).attr('data-name')){
                            lV.push($($('.o_list_table thead tr th')[i]).attr('data-name'));
                        }
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
        _commitSearch: function () {
            var self = this;
            var filters = _.invoke(this.propositions, 'get_filter').map(function (preFilter) {
                var _description = _t('Advanced search');
                if(typeof self.__parentedParent !== 'undefined'){
                     if(typeof self.__parentedParent.context !== 'undefined'){
                        if(typeof self.__parentedParent.context.lang !== 'undefined'){
                            if(self.__parentedParent.context.lang ==='en_US'){
                                _description = _t('Advanced search');
                            }else{
                                _description = _t('高度な検索');
                            }
                        }
                     }
                }

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
    });
    FilterMenu.include(My_FilterMenu);
});
