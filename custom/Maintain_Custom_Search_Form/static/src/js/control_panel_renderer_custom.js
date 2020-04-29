odoo.define('web.ControlPanelRenderer_Custom', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Domain = require('web.Domain');
var ControlPanelRenderer = require('web.ControlPanelRenderer');


var _t = core._t;
var QWeb = core.qweb;

var ControlPanelRenderer_Custom = ControlPanelRenderer.include({
//    init: function (parent, filters, fields) {
//        this._super(parent, filters);
//    },

    updateFilters: function (newFilters, filtersToRemove) {
        var newFilterIDS = this.model.createNewFilters(newFilters);
        this.model.deactivateFilters(filtersToRemove);
        this._reportNewQueryAndRender(ev);
        return newFilterIDS;
    },

    _reportNewQueryAndRender: function (ev) {
        this.trigger_up('search', this.model.getQuery());
        var state = this.model.get();
        if(ev){
            if(typeof ev.target.dropdownCategory != 'undefined'){
                if (ev.target.dropdownCategory==='filter1' && state.facets.length>0){
                    var lengthF = state.facets.length;
                    var hasFreeSearch = 0;
                    var sF = {};
                    var sT = {};

                    for (var i = lengthF-1; i>=0 ; i--){
                        var item = state.facets[i];
                        if(typeof item.filters !== 'undefined'){
                            for(var j = item.filters.length -1 ; j >=0; j--){
                                if (typeof item.filters[j].subtype !== 'undefined' ){
                                    hasFreeSearch++;
                                    sT = item.filters[j];
                                    sF = item;
                                    break;
                                }
                            }
                        }
                        if (hasFreeSearch > 0){
                            state.facets = [sF];
                            //this.state.facets[0].filters = sT;
                            break;
                        }
                    }
                }
             }
         }

        return this.renderer.updateState(state,ev);
    },

    _onFacetRemoved: function (ev) {
        ev.stopPropagation();
        var group = ev.data.group || this.renderer.getLastFacet();
        if (group) {
            this.model.deactivateGroup(group.id);
             if(ev.target.facetValues[0] ==="Free Search" || ev.target.facetValues ==='Free Search' || ev.target.facetValues[0] ==="高度な検索" || ev.target.facetValues ==='高度な検索'){
                var def = this.model.deleteFilterEverywhere(ev.data.group.filters[0].id);
             }
             this._reportNewQueryAndRender();
        }
    },

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onNewFilters: function (ev) {
        ev.stopPropagation();

        if(ev.target.dropdownCategory==='filter1'){
            var fc = this.model.get();
            if(fc.facets){
                for(var i = 0; i<fc.facets.length; i++){
                    if(fc.facets[i].id){
                        //ev.data.group.id = fc.facets[i].id;
                        this.model.deactivateGroup(fc.facets[i].id);
                        if(typeof fc.facets[i].filters !== 'undefined'){
                            for(var j = 0; j< fc.facets[i].filters.length; j++){
                                var def = this.model.deleteFilterEverywhere(fc.facets[i].filters[j].id);
                            }

                        }
                        //_onFacetRemoved(ev);
                        //var def = this.model.deleteFilterEverywhere(fc.facets[i].id);
                    }
                }

            }
            this.model.createNewFilters(ev.data.filters);
            this._reportNewQueryAndRender(ev);
        }else{
            this.model.createNewFilters(ev.data.filters)
            this._reportNewQueryAndRender(ev);
        }


    },

});

ControlPanelRenderer.include(ControlPanelRenderer_Custom);

});
