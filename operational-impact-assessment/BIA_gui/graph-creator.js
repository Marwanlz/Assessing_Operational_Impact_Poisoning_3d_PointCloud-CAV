(function(d3, saveAs, Blob, UndoManager, alertify){
  "use strict";

  // TODO add user settings
  let settings = {
    appendElSpec: "#graph"
  };

  const displayType = {
    PROBABILITY: "Probability",
    TEMPORAL : "Temporal"
  };

  const getButtonText = {
    PROBABILITY: "Get Impact Probability",
    TEMPORAL: "Get Critical Time"
  };

  const nodeType = {
    ASSET: "Asset",
    BUSINESS: "Business",
    SHOCK: "Shock"
  };

  const formNodeMapping = {
    "Asset": "ellipse",
    "Business": "rectangle",
    "Shock": "hexagon"
  };

  //Margin left for the panel
  const LEFTPANELSIZE = 315;

  // define graphcreator object
  let GraphCreator = function(svg, nodes, edges, config){
    let thisGraph = this;
        thisGraph.idct = 0;
    if (!config) {
        config = {};
    }
    let default_config = GraphCreator.prototype.consts;
    for (let key in default_config) {
        if (default_config.hasOwnProperty(key) && !config.hasOwnProperty(key)) {
            config[key] = default_config[key];
        }
    }
    this.consts = config;
    this.undo_manager = new UndoManager();
    thisGraph.nodes = nodes || [];
    thisGraph.edges = edges || [];
    thisGraph.state = {
      displayType: displayType.PROBABILITY,
      selectedNode: null,
      selectedEdge: null,
      mouseDownNode: null,
      mouseDownLink: null,
      justDragged: false,
      justScaleTransGraph: false,
      lastKeyDown: -1,
      shiftNodeDrag: false,
    };
    // define arrow markers for graph links
    let defs = svg.append('svg:defs');
    defs.append('svg:marker')
      .attr('id', 'end-arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('markerWidth', 3.5)
      .attr('markerHeight', 3.5)
      .attr('orient', 'auto')
      .append('svg:path')
      .attr('d', 'M0,-5L10,0L0,5');
    // define arrow markers for leading arrow
    defs.append('svg:marker')
      .attr('id', 'mark-end-arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 7)
      .attr('markerWidth', 3.5)
      .attr('markerHeight', 3.5)
      .attr('orient', 'auto')
      .append('svg:path')
      .attr('d', 'M0,-5L10,0L0,5');

    thisGraph.svg = svg;
    thisGraph.svgG = svg.append("g")
          .classed(thisGraph.consts.graphClass, true);
    let svgG = thisGraph.svgG;

    // displayed when dragging between nodes
    thisGraph.dragLine = svgG.append('svg:path')
          .attr('class', 'link dragline hidden')
          .attr('d', 'M0,0L0,0')
          .style('marker-end', 'url(#mark-end-arrow)');

    // svg nodes and edges
    thisGraph.gedges = svgG.append("g").selectAll("g");
    thisGraph.gnodes = svgG.append("g").selectAll("g");
    thisGraph.drag = d3.behavior.drag()
          .origin(function(d){
            return {x: d.x, y: d.y};
          })
          .on("drag", function(args){
            thisGraph.state.justDragged = true;
            thisGraph.dragmove.call(thisGraph, args);
          })
          .on("dragend", function() {
            // todo check if edge-mode is selected
          });

    // listen for key events
    thisGraph._toggle_key_events_listen = function (enable) {
        if (enable) {
            d3.select(window).on("keydown", function(){
              thisGraph.svgKeyDown.call(thisGraph);
            })
            .on("keyup", function(){
              thisGraph.svgKeyUp.call(thisGraph);
            });
        }
        else {
            d3.select(window).on("keydown", null)
            .on("keyup", null);
        }
    };
    thisGraph._toggle_key_events_listen(true);

    // listen for mouse events
    svg.on("mousedown", function(d){thisGraph.svgMouseDown.call(thisGraph, d);});
    svg.on("mouseup", function(d){thisGraph.svgMouseUp.call(thisGraph, d);});

    // listen for dragging
    let dragSvg = d3.behavior.zoom()
          .scaleExtent([thisGraph.consts.zoomMinScale, thisGraph.consts.zoomMaxScale])
          .on("zoom", function(){
            if (d3.event.sourceEvent.shiftKey){
              // TODO  the internal d3 state is still changing
              return false;
            } else{
              thisGraph.zoomed.call(thisGraph);
            }
            return true;
          })
          .on("zoomend", function(){
            d3.select('body').style("cursor", "auto");
          });

    thisGraph.dragSvg = dragSvg;
    svg.call(dragSvg).on("dblclick.zoom", null);

    // listen for resize
    window.onresize = function(){thisGraph.updateWindow(svg);};

    // handle download data
    d3.select("#download-input").on("click", function(){
      thisGraph._toggle_key_events_listen(false);
      alertify.prompt("Save graph", "How do you want to name the file?", "BIA_graph.json",
              function save(e, name) {
                  thisGraph._toggle_key_events_listen(true);
                  if (name && name.length > 0) {
                      let saveEdges = [];
                      thisGraph.edges.forEach(function(val, i){
                        saveEdges.push({
                          source: val.source.id, target: val.target.id,
                          label: val.label,
                          propagationProba_fwd: val.propagationProba_fwd,
                          propagationProba_bwd: val.propagationProba_bwd,
                          propagationTime_fwd: val.propagationTime_fwd,
                          propagationTime_bwd: val.propagationTime_bwd,
                          form: val.form, stroke: val.stroke, fint: val.fint,
                          color: val.color
                        });
                      });
                      let blob = new Blob([window.JSON.stringify({"nodes": thisGraph.nodes, "edges": saveEdges})], {type: "text/plain;charset=utf-8"});
                      saveAs(blob, name);
                  }
                  else {
                      alertify.alert("That is not a valid name. >:@");
                  }
              },
              function noop() {
                  thisGraph._toggle_key_events_listen(true);
              }
              );
    });

    // save the graph as an image
    d3.select('#download-image').on('click', function() {
      thisGraph._toggle_key_events_listen(false);
      alertify.prompt("Export graph to PNG image", "How do you want to name the file?", "BIA_graph.png",
              function save(e, name) {
                  thisGraph._toggle_key_events_listen(true);
                  if (name && name.length > 0) {
                    let svg = thisGraph.svg;
                    let width = svg.attr('width');
                    let height = svg.attr('height');

                    save_svg_as_png_image(svg.node(), width, height, function (dataBlob, filesize) {
                        saveAs(dataBlob, name);
                    });
                  }
                  else {
                      alertify.alert("That is not a valid name. >:@");
                  }
              },
              function noop() {
                  thisGraph._toggle_key_events_listen(true);
              }
              );
    });


    // handle uploaded data
    d3.select("#upload-input").on("click", function(){
      document.getElementById("hidden-file-upload").click();
    });
    d3.select("#hidden-file-upload").on("change", function(){
      if (window.File && window.FileReader && window.FileList && window.Blob) {
        let uploadFile = this.files[0];
        console.log("uploadFile");
        console.log(uploadFile);
        let filereader = new window.FileReader();
        console.log("filereader");
        console.log(filereader);

        filereader.onload = function(){
          let txtRes = filereader.result;
          console.log("txtRes");
          console.log(txtRes);
          // TODO better error handling
          try{
            let json_graph = JSON.parse(txtRes);
            thisGraph.load_graph_from_json(json_graph);
            thisGraph.centerGraph();
          }catch(err){
            alertify.alert('Ups!', "Error parsing uploaded file\nerror message: " + err.message);
            return;
          }
        };
        console.log("hello ça va");
        console.log(uploadFile);
        filereader.readAsText(uploadFile);
      } else {
        alertify.alert('Ups!', "Your browser won't let you save this graph " +
                               "-- try upgrading your browser to IE 10+ or Chrome or Firefox.");
      }

    });

    // handle delete graph
    d3.select("#delete-graph").on("click", function(){
      alertify.confirm("Delete graph",
                       "Are you sure that you want to delete this graph?",
                        function () {
                          thisGraph.deleteGraph();
                        },
                        function noop() {});
    });

    // center the graph
    d3.select("#center-graph").on("click", function(){
      thisGraph.centerGraph();
    });

    // Radio button to change displayType.
    const button_displayType = d3.selectAll('.button_displayType');
    button_displayType.on('change', function(d) {
      let newDisplayType = this.value;
      if (thisGraph.state.displayType != newDisplayType){
        thisGraph.changeDisplayType(newDisplayType);
      }
    });



    // Button to get Impact from the Python API
    const button_getImpact = d3.selectAll('#button_getImpact');
    button_getImpact.on('click', function(e) {
      if (this.textContent == getButtonText.PROBABILITY){
        thisGraph.getImpactFromAPI();
      }
      else{
        thisGraph.getCriticalTimeFromAPI();
      }
    });

    // Button to get Criticality from the Python API
    const button_getCriticality = d3.selectAll('#button_getCriticality');
    button_getCriticality.on('click', function(e) {
      thisGraph.getCriticalityFromAPI();
    });
  };

  GraphCreator.prototype.getImpactFromAPI = function(){
    let thisGraph = this;
    let data_to_send = thisGraph.get_graph_to_json();
    console.log("Send Impact computation request to the Python API");
    console.log(data_to_send);
    // Change the displayed impact result
    d3.select("#get_button_result").text("Processing ...");
    let biaBackendAddress = thisGraph.consts.biaBackendAddress;
    let service = thisGraph.consts.urlComputeBusinessImpact;
    let service_url = `${biaBackendAddress}/${service}`;
    $.ajax({
      type: 'post',
      url: service_url,
      async: true,
      dataType: "json",
      contentType: "application/json",
      data: data_to_send,
      success: function (response) {
        for(const response_node of response){
          let node_id = response_node.id;
          let proba_bImpact = response_node.proba_bImpact
          let color_impact = thisGraph.getColorFromImpact(proba_bImpact);
          proba_bImpact = String(Math.round(proba_bImpact*100)/100);
          let b_gnode_size = 0;
          let b_gnode = thisGraph.gnodes.filter(function(d){
            if (d.id === node_id){
              d.color = color_impact;
              b_gnode_size = d.size;
              return true;
            };
          });
          console.log(b_gnode);
          b_gnode.select(".business_impact_box").remove();
          // Compute the height to display the value on the top of the node
          let dy_b_box = -1 * (b_gnode_size / 1000 *2.08 + 16.68)
          let impact_el = b_gnode.append("text")
                                  .attr("class", "business_impact_box")
                                  .attr("dy", dy_b_box)
                                  .attr("text-anchor", "middle")
                                  .attr("font-size", "20")
                                  .attr("font-weight","bold")
                                  .style('fill', 'red')
                                  .text(proba_bImpact);
        }
      }
    }).done(function (data) {
        // Change the displayed impact result
        thisGraph.updateGraph();
        d3.select("#get_button_result").text("Done");
    });
  };

  GraphCreator.prototype.getCriticalTimeFromAPI = function(){
    let thisGraph = this;
    this.resetEdges();
    let data_to_send = thisGraph.get_graph_to_json();
    console.log("Send Critical Time computation request to the Python API");
    console.log(data_to_send);
    // Change the displayed impact result
    d3.select("#get_button_result").text("Processing ...");
    let biaBackendAddress = thisGraph.consts.biaBackendAddress;
    let service = thisGraph.consts.urlComputeCriticalTime;
    let service_url = `${biaBackendAddress}/${service}`;
    $.ajax({
      type: 'post',
      url: service_url,
      async: true,
      dataType: "json",
      contentType: "application/json",
      data: data_to_send,
      success: function (response) {
        console.log(response);
        let path_value = response[0];
        let path = response[1];
        let edge_color = thisGraph.consts.colorEdgePath;
        let edge_stroke = thisGraph.consts.strokeEdgePath;
        for (let i = 0; i < path.length - 1; ++i) {
          let source_id = path[i];
          let target_id = path[i+1];
          thisGraph.gedges.filter(function(e){
              if ((e.source.id === source_id && e.target.id === target_id) ||
                (e.source.id === target_id  && e.target.id === source_id)) {
              e.color = edge_color;
              e.stroke = edge_stroke;
            };
          });
        }
      }
    }).done(function (data) {
        // Change the displayed impact result
        thisGraph.updateGraph();
        let path_value  = data[0];
        let path = data[1];
        d3.select("#get_button_result").text(path_value);//"TPS critique: en gras", path_value);
    });
  };

  GraphCreator.prototype.resetEdges = function(){
    let edge_color = this.consts.colorEdgeNormal;
    let edge_stroke = this.consts.strokeEdgeNormal;
    this.gedges.each(
      function(e){
        e.color = edge_color;
        e.stroke = edge_stroke;
      }
    );
    this.updateGraph();
  };

  GraphCreator.prototype.getColorFromImpact = function(proba_bImpact){
    if (proba_bImpact < 0){
      return this.consts.colorError;
    }
    else if (proba_bImpact < this.consts.thresholdImpactLow){
      return this.consts.colorImpactLow;
    }
    else if (proba_bImpact > this.consts.thresholdImpactHigh) {
      return this.consts.colorImpactHigh;
    }
    return this.consts.colorImpactMedium;
  };

  GraphCreator.prototype.getCriticalityFromAPI = function(){
    let thisGraph = this;
    let data_to_send = thisGraph.get_graph_to_json();
    console.log("Send Criticality computation request to the Python API");
    console.log(data_to_send);
    // Change the displayed impact result
    d3.select("#criticality_result").text("Processing ...");
    let biaBackendAddress = thisGraph.consts.biaBackendAddress;
    let service = thisGraph.consts.urlComputeCriticality;
    let service_url = `${biaBackendAddress}/${service}`;
    $.ajax({
      type: 'post',
      url: service_url,
      async: true,
      dataType: "json",
      contentType: "application/json",
      data: data_to_send,
      success: function (response) {
        for(const resp_node of response){
          let node_id = resp_node.id;
          let criticality_node = resp_node.criticality_value
          let color_impact = thisGraph.getColorFromCriticality(criticality_node);
          criticality_node = String(Math.round(criticality_node*100)/100);
          let b_gnode_size = 0;
          let b_gnode = thisGraph.gnodes.filter(function(d){
            if (d.id === node_id){
              d.color = color_impact;
              b_gnode_size = d.size;
              return true;
            };
          });
          // Compute the height to display the value on the top of the node
          let dy_b_box = -1 * (b_gnode_size / 1000 *2.28 + 26)
          b_gnode.select(".criticality_node_box").remove();
          let impact_el = b_gnode.append("text")
                                  .attr("class", "criticality_node_box")
                                  .attr("dy", dy_b_box)
                                  .attr("text-anchor", "middle")
                                  .attr("font-size", "20")
                                  .attr("font-weight","bold")
                                  .style('fill', 'orange')
                                  .text(criticality_node);
        }
      }
    }).done(function (data) {
        // Change the displayed impact result
        thisGraph.updateGraph();
        d3.select("#criticality_result").text("Done");
    });
  };

  GraphCreator.prototype.getColorFromCriticality = function(criticality_node){
    if (criticality_node < 0){
      return this.consts.colorError;
    }
    else if (criticality_node < this.consts.thresholdCriticalityLow){
      return this.consts.colorCriticalityLow;
    }
    else if (criticality_node > this.consts.thresholdCriticalityHigh) {
      return this.consts.colorCriticalityHigh;
    }
    return this.consts.colorCriticalityMedium;
  };

  GraphCreator.prototype.setIdCt = function(idct){
    this.idct = idct;
  };

  GraphCreator.prototype.consts =  {
    defaultNodeTitle: "Random Asset",
    defaultNodeType: "Asset",
    defaultEdgeLabel: "0.5",
    defaultPropagationProba: 0.5,
    defaultPropagationNull: 0,
    defaultPropagationTime: 0.1,
    defaultFint: 3,
    defaultColor: "white",
    selectedClass: "selected",
    connectClass: "connect-node",
    nodeGClass: "conceptG",
    graphClass: "graph",
    BACKSPACE_KEY: 8,
    DELETE_KEY: 46,
    ENTER_KEY: 13,
    UNDO_KEY: 90, // Z
    REDO_KEY: 89, // Y
    TYPE_KEY: 84,
    nodeSize: 2000,
    nodeMargin: 7,
    continuationWordMarker: "...",
    maxWordLength: 16,
    charWidthPixel: 10,
    lineHeightPixel: 15,
    lowerTextRatio: 1.60,
    upperTextRatio: 4.0,
    zoomMinScale: 0.25,
    zoomMaxScale: 1.5,
    COLOR_INTENSITIES: 6,
    STROKES: [
        "none", // contiguous line
        "5, 2",
        "10, 5",
        "10, 15",
        "5, 10",
        "10, 5, 5, 5, 5, 5",
        "5, 2, 2, 2, 2, 2",
    ],
    thresholdImpactLow: 0.100,
    thresholdImpactHigh: 0.200,
    thresholdCriticalityLow: 0.333,
    thresholdCriticalityHigh: 0.666,
    colorImpactLow: "#95cc00", // green
    colorImpactMedium: "#fbc246", // yellow
    colorImpactHigh: "#c91c1f", // red
    colorCriticalityLow: "#95cc00", // green
    colorCriticalityMedium: "#fbc246", // yellow
    colorCriticalityHigh: "#c91c1f", // red
    colorError: "white",
    colorEdgeNormal: "black",
    colorEdgePath: 2,
    strokeEdgeNormal: 0 ,
    strokeEdgePath: 2,
    biaBackendAddress: "https://bia-backend.soccrates.xyz",
    urlComputeBusinessImpact: "computeBusinessImpact_GUI",
    urlComputeCriticalTime: "computeCriticalTime_GUI",
    urlComputeCriticality: "computeCriticality_GUI",
    urlGetRequestGraph: "getRequestGraph",
    urlGetDefaultGraph: "getDefaultGraph"

  };

  /* PROTOTYPE FUNCTIONS */
  GraphCreator.prototype.load_graph_from_json = function (json_graph) {
    let thisGraph = this;
    thisGraph.deleteGraph();
    thisGraph.nodes = json_graph.nodes;
    let maxIdCt = 0;
    for (let i = 0; i < thisGraph.nodes.length; ++i) {
        maxIdCt = (maxIdCt < thisGraph.nodes[i].id) ? thisGraph.nodes[i].id : maxIdCt;
        // backward compatibility for missing fields
        let node = thisGraph.nodes[i];
        thisGraph.nodes[i].fint = node.fint || this.consts.defaultFint;
        thisGraph.nodes[i].color = this.consts.defaultColor;
        thisGraph.updateNodeForm(node, node.type);
        thisGraph.nodes[i].size = 2000;
    }
    thisGraph.setIdCt(maxIdCt + 1);
    let newEdges = json_graph.edges;
    newEdges.forEach(function(e, i){
      newEdges[i] = {
                  source: thisGraph.nodes.filter(function(n){return n.id == e.source;})[0],
                  target: thisGraph.nodes.filter(function(n){return n.id == e.target;})[0],
                  label: e.label,
                  propagationProba_fwd: e.propagationProba_fwd,
                  propagationProba_bwd: e.propagationProba_bwd,
                  propagationTime_fwd: e.propagationTime_fwd,
                  propagationTime_bwd: e.propagationTime_bwd,
                  color: newEdges[i].color, stroke: newEdges[i].stroke,
                  form: e.form, size: e.size
                  };
    });
    thisGraph.edges = newEdges;
    thisGraph.updateGraph();
    thisGraph.undo_manager.clear();
  };


  GraphCreator.prototype.get_graph_to_json = function () {
    let thisGraph = this;
    let sendEdges = [];
    thisGraph.edges.forEach(function(val, i){
      sendEdges.push({
        source: val.source.id, target: val.target.id,
        propagationProba_fwd: val.propagationProba_fwd,
        propagationProba_bwd: val.propagationProba_bwd,
        propagationTime_fwd: val.propagationTime_fwd,
        propagationTime_bwd: val.propagationTime_bwd
      });
    });
    let sendNodes = [];
    thisGraph.nodes.forEach(function(val, i){
      sendNodes.push({id: val.id, title: val.title, type: val.type.toString()});
    });
    return window.JSON.stringify({"nodes": sendNodes, "edges": sendEdges});
  };

  GraphCreator.prototype.centerGraph = function () {
    let thisGraph = this;
    // find the mass center of the graph
    let x = 0, y = 0;
    thisGraph.nodes.forEach(function (d) {
      x += d.x;
      y += d.y;
    });
    let nnodes = thisGraph.nodes.length || 1;
    x = x / nnodes;
    y = y / nnodes;
    // find the difference between the mass center and the center of the canvas
    let w = thisGraph.svg.attr("width");
    let h = thisGraph.svg.attr("height");
    let dx = (w/2) - x;
    let dy = (h/2) - y;
    thisGraph.dragSvg.translate([dx,dy]);
    thisGraph.dragSvg.scale(1);
    thisGraph.zoomed.call(thisGraph);
    thisGraph.updateGraph();
  };

  GraphCreator.prototype.dragmove = function(d) {
    let thisGraph = this;
    if (thisGraph.state.shiftNodeDrag){
      let moveto = `M${d.x},${d.y}`;
      let lineto = `L${d3.mouse(thisGraph.svgG.node())[0]},${d3.mouse(thisGraph.svgG.node())[1]}`;
      thisGraph.dragLine.attr('d', `${moveto}${lineto}`);
    } else{
      d.x += d3.event.dx;
      d.y +=  d3.event.dy;
      thisGraph.updateGraph();
    }
  };

  GraphCreator.prototype.deleteGraph = function(){
    let thisGraph = this;
    thisGraph.nodes = [];
    thisGraph.edges = [];
    thisGraph.updateGraph();
  };

  /* select all text in element: taken from http://stackoverflow.com/questions/6139107/programatically-select-text-in-a-contenteditable-html-element */
  GraphCreator.prototype.selectElementContents = function(el) {
    let range = document.createRange();
    range.selectNodeContents(el);
    let sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  };


  /* insert svg line breaks: taken from http://stackoverflow.com/questions/13241475/how-do-i-include-newlines-in-labels-in-d3-charts */
  GraphCreator.prototype.insertTitleLinebreaks = function (gEl, d) {
    let title = d.title;
    let lineHeightPixel = this.consts.lineHeightPixel;
    let charWidthPixel = this.consts.charWidthPixel;
    let lowerTextRatio = this.consts.lowerTextRatio;
    let upperTextRatio = this.consts.upperTextRatio;
    let perfectTextRatio = lowerTextRatio + ((upperTextRatio - lowerTextRatio)/2);
    let nodeMargin = this.consts.nodeMargin;
    let words = d.title.trim().split(/\s+/g);
    // replace tooo long words by shorter ones
    let continuation_marker_length = this.consts.continuationWordMarker.length;
    for (let i = 0; i < words.length; ++i) {
        if (words[i].length > this.consts.maxWordLength) {
            words[i] = words[i].substr(0, this.consts.maxWordLength-continuation_marker_length) +
                            this.consts.continuationWordMarker;
        }
    }
    let lines = words;
    let ratio = (charWidthPixel * lines.length) / (lineHeightPixel * 1);
    let max_line_length = lines[0].length;
    while (1) {
        let old_lines = lines;
        let old_ratio = ratio;
        // try to put small words in a single line
        let new_lines = [];
        let last_line_length = 0;
        for (let i = 0; i < words.length; i++) {
            let l = words[i].length;
            if (last_line_length + l + 1 > max_line_length || new_lines.length === 0) {
                new_lines.push(words[i]);
                last_line_length = l;
            }
            else {
                new_lines[new_lines.length - 1] += (" " + words[i]);
                last_line_length += l + 1;
            }
        }
        lines = new_lines;
        let width  = charWidthPixel  * max_line_length;
        let height = lineHeightPixel * lines.length;
        ratio  = width / height;
        if (ratio > lowerTextRatio && ratio < upperTextRatio) { // good enough
            break;
        }
        else if (ratio == old_ratio) { // we didn't improved too much
            break;
        }
        else if (ratio < lowerTextRatio) {  // too many lines, continue trying to join them
            if (lines.length < 2) {
                break; // we don't have lines to join, finish here
            }
        }
        else { // too few lines, try to revert the last join, if its ratio is better
           if (Math.abs(old_ratio - perfectTextRatio) < Math.abs(ratio - perfectTextRatio)) {
               lines = old_lines;
           }
           break;
        }

        // search for two consecutive lines to join that sum the minimal length greather than the current maximum
        let min_joined_lines_length = lines[0].length + lines[1].length + 1;
        let min_at = 0;
        for (let i = 0; i < lines.length - 1; i++) {
            let l = lines[i].length + lines[i+1].length + 1;
            if (l > max_line_length && l < min_joined_lines_length) {
                min_joined_lines_length = l;
                min_at = i;
            }
        }

        // join them
        lines[min_at] = lines[min_at] + " " + lines[min_at+1];
        lines.splice(min_at + 1, 1);

        // update the max line length with the new line added
        if (lines[min_at].length > max_line_length) {
            max_line_length = lines[min_at].length;
        }
        else {
            break; // this was my best effort, sorry
        }
    }

    let el = gEl.append("text")
          .attr("text-anchor","middle")
          .attr("dy", -(lines.length-1)*(lineHeightPixel / 2) + nodeMargin);

    for (let i = 0; i < lines.length; i++) {
      let tspan = el.append('tspan').text(lines[i]);
      if (i > 0)
        tspan.attr('x', 0).attr('dy', lineHeightPixel);

    let width  = charWidthPixel  * max_line_length;
    let height = lineHeightPixel * lines.length;
    // Update size value of the edge
    let scalingFactor = 100;
    d.size = Math.max(width, height) * scalingFactor;
    }

  };

  GraphCreator.prototype.insertEdgeLabel = function (gEl, d) {
      let PRECISION_NUMBER = 2
      let txt_label_fwd = String(d.label_fwd.toPrecision(PRECISION_NUMBER));
      let txt_label_bwd = String(d.label_bwd.toPrecision(PRECISION_NUMBER));
      let isRotated = d.target.x < d.source.x;
      // Rotation for right to left labels
      let fwd_el = gEl.append("text")
              .attr('transform', function (d) {
                  if (isRotated) {
                    let middle_x = (d.target.x + d.source.x)/2;
                    let middle_y = (d.target.y + d.source.y)/2;
                    // return 'rotate(180'+ ',' + middle_x + ',' + middle_y + ')';
                    return `rotate(180,${middle_x},${middle_y})`;
                  } else {
                    return 'rotate(0)';
                  }
              })
              .attr("dy", -5)
          .attr("text-anchor", "middle");
      // Adding the foward label
      fwd_el.append('textPath')
          .attr('xlink:href', function (d, i) {
                  return `#${d.source.id}_${d.target.id}`;
          })
          .attr("font-size", "18")
          .style("text-anchor",  isRotated ? "end" : "start")
          .style("pointer-events", "none")
          //Set offset position according if it has been rotated by 180.
          .attr("startOffset", isRotated ? "45%" : "55%")
          .attr("stroke", "#FFF")
          .attr("font-weight","bold")
          .attr("paint-order", "stroke")
          .attr("stroke-width", "2px")
          .style('fill', 'darkBlue')
          .text(txt_label_fwd);

      // Rotation for right to left labels
      let bwd_el = gEl.append("text")
          .attr('transform', function (d) {
              if (isRotated) {
                  let middle_x = (d.target.x + d.source.x)/2;
                  let middle_y = (d.target.y + d.source.y)/2;
                  return `rotate(180,${middle_x},${middle_y})`;
                } else {
                  return 'rotate(0)';
                }
              })
            .attr("dy", -5)
            .attr("text-anchor", "middle");

      //Adding the backward label
      bwd_el.append('textPath')
          .attr('xlink:href', function (d, i) {
            return `#${d.source.id}_${d.target.id}`;
          })
          .attr("font-size", "18")
          //Set offset position according if it has been rotated by 180.
          .style("text-anchor", isRotated ? "start" : "end")
          .attr("startOffset", isRotated ? "55%" : "45%")
          .style("pointer-events", "none")
          .attr("stroke", "#FFF")
          .attr("paint-order", "stroke")
          .attr("stroke-width", "2px")
          .style('fill', 'blue')
          .text(txt_label_bwd);
  };

  GraphCreator.prototype.replaceSelectEdge = function(d3Path, edgeData){
    let thisGraph = this;
    d3Path.classed(thisGraph.consts.selectedClass, true);
    if (thisGraph.state.selectedEdge){
      thisGraph.removeSelectFromEdge();
    }
    thisGraph.state.selectedEdge = edgeData;
  };

  GraphCreator.prototype.replaceSelectNode = function(d3Node, nodeData){
    let thisGraph = this;
    d3Node.classed(this.consts.selectedClass, true);
    if (thisGraph.state.selectedNode){
      thisGraph.removeSelectFromNode();
    }
    thisGraph.state.selectedNode = nodeData;
  };

  GraphCreator.prototype.removeSelectFromNode = function(){
    let thisGraph = this;
    thisGraph.gnodes.filter(function(cd){
      return cd.id === thisGraph.state.selectedNode.id;
    }).classed(thisGraph.consts.selectedClass, false);
    thisGraph.state.selectedNode = null;
  };

  GraphCreator.prototype.removeSelectFromEdge = function(){
    let thisGraph = this;
    thisGraph.gedges.filter(function(cd){
      return cd === thisGraph.state.selectedEdge;
    }).select("path").classed(thisGraph.consts.selectedClass, false);
    thisGraph.state.selectedEdge = null;
  };

  // mousedown on edge
  GraphCreator.prototype.pathMouseDown = function(d3path, d){
    let thisGraph = this,
        state = thisGraph.state;
    d3.event.stopPropagation();
    state.mouseDownLink = d;

    if (state.selectedNode){
      thisGraph.removeSelectFromNode();
    }

    let prevEdge = state.selectedEdge;
    if (!prevEdge || prevEdge !== d){
      thisGraph.replaceSelectEdge(d3path, d);
    } else{
      thisGraph.removeSelectFromEdge();
    }
  };

  // mousedown on node
  GraphCreator.prototype.circleMouseDown = function(d3node, d){
    let thisGraph = this,
        state = thisGraph.state;
    d3.event.stopPropagation();
    state.mouseDownNode = d;
    if (d3.event.shiftKey){
      state.shiftNodeDrag = d3.event.shiftKey;
      let moveto = `M${d.x},${d.y}`
      let lineto = `L${d.x},${d.y}`
      thisGraph.dragLine.classed('hidden', false).attr('d', `${moveto}${lineto}`);
      return;
    }
  };

  /* place editable title on node in place of svg text */
  GraphCreator.prototype.editInfoOfNode = function(d3node, d, is_a_new_node){
    let thisGraph= this;
    // Disable key events
    thisGraph._toggle_key_events_listen(false);
    // Show modal window
    $("#nodeModal").modal();
    //Put old attributes values in the form
    $('select[name="txt_node_type"]').val(d.type);
    $('input[name="txt_node_title"]').val(d.title);
    $('input[name="txt_node_uuid"]').val(d.uuid);
    $('input[name="txt_node_ip"]').val(d.ip);
    //Submit clicked
    $('#node_submit').unbind('click').click(function () {
      //Remove old value displayed
      d3node.selectAll("text").remove();
      //Get new values
      let new_node_type = $('select[name="txt_node_type"]').val();
      let new_node_title = $('input[name="txt_node_title"]').val();
      let new_node_uuid = $('input[name="txt_node_uuid"]').val();
      let new_node_ip = $('input[name="txt_node_ip"]').val();

      // Update Node with new values
      thisGraph.updateNode(d3node, d, new_node_title, new_node_type, new_node_uuid, new_node_ip, is_a_new_node);
      // Enable key events
      thisGraph._toggle_key_events_listen(true);
    });
    //The windows is hidden _ enable key events
    $('#nodeModal').on('hidden.bs.modal', function () {
      // Enable key events
      thisGraph._toggle_key_events_listen(true);
    });
    //add enter key event in forms
    $("#txt_node_title").keypress(function(e) {
      if(e.which == 13) {
        $("#node_submit").click();
      }
      })
  };

  GraphCreator.prototype.changeInfoOfEdge = function (d3edge, d) {
      let thisGraph = this;
      // Disable key events
      thisGraph._toggle_key_events_listen(false);
      // Show modal window
      $("#edgeModal").modal();
      //Put old attributes values in the form
      $('input[name="txt_propagationProba_fwd"]').val(d.propagationProba_fwd);
      $('input[name="txt_propagationProba_bwd"]').val(d.propagationProba_bwd);
      $('input[name="txt_propagationTime_fwd"]').val(d.propagationTime_fwd);
      $('input[name="txt_propagationTime_bwd"]').val(d.propagationTime_bwd);
      //Submit clicked
      $('#edge_submit').unbind('click').click(function () {
        //Remove old value displayed
        console.log("d3edge");
        console.log(d3edge);
        d3edge.selectAll("text").remove();
        //Get new values
        let propagationProba_fwd = parseFloat($('input[name="txt_propagationProba_fwd"]').val());
        let propagationProba_bwd = parseFloat($('input[name="txt_propagationProba_bwd"]').val());
        let propagationTime_fwd = parseFloat($('input[name="txt_propagationTime_fwd"]').val());
        let propagationTime_bwd = parseFloat($('input[name="txt_propagationTime_bwd"]').val());
        // Check the limits of Probabilities
        if (isNaN(propagationProba_fwd) || propagationProba_fwd<0) propagationProba_fwd=0;
        if (propagationProba_fwd>1) propagationProba_fwd=1;
        if (isNaN(propagationProba_bwd) || propagationProba_bwd<0) propagationProba_bwd=0;
        if (propagationProba_bwd>1) propagationProba_bwd=1;
        //Check the limit of propagation Time
        if (isNaN(propagationTime_fwd) || propagationTime_fwd<0) propagationTime_fwd=0;
        if (isNaN(propagationTime_bwd) || propagationTime_bwd<0) propagationTime_bwd=0;

        d.propagationProba_fwd = propagationProba_fwd;
        d.propagationProba_bwd = propagationProba_bwd;
        d.propagationTime_fwd = propagationTime_fwd;
        d.propagationTime_bwd = propagationTime_bwd;

        let label_fwd = propagationTime_fwd;
        let label_bwd = propagationTime_bwd;
        if (thisGraph.state.displayType == displayType.PROBABILITY){
          label_fwd = propagationProba_fwd;
          label_bwd = propagationProba_bwd;
        }
        //Set the new values of the edge
        d.label_fwd = label_fwd;
        d.label_bwd = label_bwd;
        //Apply the value
        console.log("update Edge Value");
        console.log(d);
        thisGraph.insertEdgeLabel(d3edge, d);
      });
      //The windows is hidden _ enable key events
      $('#edgeModal').on('hidden.bs.modal', function () {
        // Enable key events
        thisGraph._toggle_key_events_listen(true);
      });
      //add enter key event in forms
      $("#txt_propagationProba_bwd").keypress(function(e) {
        if(e.which == 13) {
          $("#edge_submit").click();
        }
      })
      $("#txt_propagationProba_fwd").keypress(function(e) {
        if(e.which == 13) {
          $("#edge_submit").click();
        }
      })
      $("#txt_propagationTime_fwd").keypress(function(e) {
        if(e.which == 13) {
          $("#edge_submit").click();
        }
      })
        /*
        $("#txt_propagationTime_bwd").keypress(function(e) {
          if(e.which == 13) {
            $("#edge_submit").click();
          }
        })*/
  };

  GraphCreator.prototype.updateNode = function(d3node, d, new_title, new_nodeType, new_node_uuid, new_node_ip, is_a_new_node) {
    let thisGraph = this;
    let old_title = d.title;
    let old_type = d.type;
    let old_uuid = d.uuid;
    let old_ip = d.ip;

    d3node.selectAll("text").remove();
    d.title = new_title;
    thisGraph.insertTitleLinebreaks(d3node, d);
    d.type = new_nodeType;
    thisGraph.updateNodeForm(d, new_nodeType);
    d.uuid = new_node_uuid;
    d.ip = new_node_ip;
    thisGraph.updateGraph();

    if (!is_a_new_node) {
      thisGraph.undo_manager.add({
              undo: function () {
                  thisGraph.updateNode(d3node, d, old_title, old_type, old_uuid, old_ip);
              },
              redo: function () {
                  thisGraph.updateNode(d3node, d, new_title, new_nodeType, new_node_uuid, new_node_ip);
              }
          });
    }
  };

  GraphCreator.prototype.updateNodeForm = function(d, new_nodeType) {
    d.form = formNodeMapping[new_nodeType];
  };

  // mouseup on nodes
  GraphCreator.prototype.circleMouseUp = function(d3node, d){
    let thisGraph = this,
        state = thisGraph.state,
        consts = thisGraph.consts;
    // reset the states
    state.shiftNodeDrag = false;
    d3node.classed(consts.connectClass, false);

    let mouseDownNode = state.mouseDownNode;

    if (!mouseDownNode) return;

    thisGraph.dragLine.classed("hidden", true);

    if (mouseDownNode !== d){
      // we're in a different node: create new edge for mousedown edge and add to graph
      let newEdge = {
        source: mouseDownNode, target: d,
        label_fwd: consts.defaultEdgeLabel,
        label_bwd: consts.defaultEdgeLabel,
        propagationProba_fwd: consts.defaultPropagationProba,
        propagationProba_bwd: consts.defaultPropagationNull,
        propagationTime_fwd: consts.defaultPropagationTime,
        propagationTime_bwd: consts.defaultPropagationNull,
        color: 0, stroke: 0
      };
      let filtRes = thisGraph.gedges.filter(function(d){
        if (d.source === newEdge.target && d.target === newEdge.source){
          thisGraph.edges.splice(thisGraph.edges.indexOf(d), 1);
        }
        return d.source === newEdge.source && d.target === newEdge.target;
      });
      if (!filtRes[0].length){
        thisGraph.addEdge(newEdge);
        console.log("Add new Edge");
        thisGraph.updateGraph();
        let d3NewEdge = thisGraph.gedges.filter(function(dval){
          return dval.source === newEdge.source && dval.target === newEdge.target;
        });
        thisGraph.changeInfoOfEdge(d3NewEdge, newEdge);
      }
    } else{
      // we're in the same node
      if (state.justDragged) {
        // dragged, not clicked
        state.justDragged = false;
      } else{
        // clicked, not dragged
        if (d3.event.ctrlKey){
          // shift-clicked node: edit node
          let d3txt = thisGraph.editInfoOfNode(d3node, d);
        } else{
          if (state.selectedEdge){
            thisGraph.removeSelectFromEdge();
          }
          let prevNode = state.selectedNode;

          if (!prevNode || prevNode.id !== d.id){
            thisGraph.replaceSelectNode(d3node, d);
          } else{
            thisGraph.removeSelectFromNode();
          }
        }
      }
    }
    state.mouseDownNode = null;
    return;

  }; // end of gnodes mouseup

  // mouseup on edge
  GraphCreator.prototype.EdgeMouseUp = function (d3node, d) {
      let thisGraph = this,
          state = thisGraph.state,
          consts = thisGraph.consts;
      // reset the states
      state.shiftNodeDrag = false;
      // clicked, not dragged
      if (d3.event.ctrlKey) {
          // shift-clicked node: edit text content:
          thisGraph.changeInfoOfEdge(d3node, d);
      }
  }; // end of edge mouseup

  // mousedown on main svg
  GraphCreator.prototype.svgMouseDown = function(){
    this.state.graphMouseDown = true;
  };

  // mouseup on main svg
  GraphCreator.prototype.svgMouseUp = function(){
    let thisGraph = this,
        consts = thisGraph.consts,
        state = thisGraph.state;
    if (state.justScaleTransGraph) {
      // dragged not clicked
      state.justScaleTransGraph = false;
    } else if (state.graphMouseDown && d3.event.shiftKey){
      // clicked not dragged from svg
      let xycoords = d3.mouse(thisGraph.svgG.node()),
          d = {id: thisGraph.idct++, title: consts.defaultNodeTitle,
            type: consts.defaultNodeType, x: xycoords[0], y: xycoords[1],
            size: consts.nodeSize, form: formNodeMapping[nodeType.ASSET],
            color: consts.defaultColor, stroke: 0, fint: consts.defaultFint};
      thisGraph.addNode(d);
      thisGraph.updateGraph();
      // make  node immediently editable
      thisGraph.editInfoOfNode(thisGraph.gnodes.filter(function(dval){
        return dval.id === d.id;
      }), d, true);
    } else if (state.shiftNodeDrag){
      // dragged from node
      state.shiftNodeDrag = false;
      thisGraph.dragLine.classed("hidden", true);
    }
    state.graphMouseDown = false;
  };

  // keydown on main svg
  GraphCreator.prototype.svgKeyDown = function() {
    let thisGraph = this,
        state = thisGraph.state,
        consts = thisGraph.consts;
    // make sure repeated key presses don't register for each keydown
    //if(state.lastKeyDown !== -1) return;

    state.lastKeyDown = d3.event.keyCode;
    let selectedNode = state.selectedNode,
        selectedEdge = state.selectedEdge;

    switch(d3.event.keyCode) {
    case consts.BACKSPACE_KEY:
    case consts.DELETE_KEY:
      d3.event.preventDefault();
      if (selectedNode){
        thisGraph.deleteNodeAndItsEdges(selectedNode);
        state.selectedNode = null;
        thisGraph.updateGraph();
      } else if (selectedEdge){
        thisGraph.deleteEdge(selectedEdge);
        state.selectedEdge = null;
        thisGraph.updateGraph();
      }
      break;
    case consts.TYPE_KEY:
      thisGraph.changeDisplayType();
      break;
    case consts.UNDO_KEY:
      if (d3.event.ctrlKey) {
        d3.event.preventDefault();
        thisGraph.undo_manager.undo();
        thisGraph.updateGraph();
      }
      break;
    case consts.REDO_KEY:
      if (d3.event.ctrlKey) {
        d3.event.preventDefault();
        thisGraph.undo_manager.redo();
        thisGraph.updateGraph();
      }
      break;
    }
  };

  GraphCreator.prototype.svgKeyUp = function() {
    this.state.lastKeyDown = -1;
  };

  // call to propagate changes to graph
  GraphCreator.prototype.updateGraph = function(){
    let thisGraph = this,
        consts = thisGraph.consts,
        state = thisGraph.state;
    let MAX_INT_IDX = consts.COLOR_INTENSITIES - 1;
    thisGraph.gedges = thisGraph.gedges.data(thisGraph.edges, function(d){
      return String(d.source.id) + "+" + String(d.target.id);
    });
    let gedges = thisGraph.gedges;
    // update existing gedges
    gedges.select("path")
      .style('marker-mid','url(#end-arrow)')
      .classed(consts.selectedClass, (d) => d === state.selectedEdge)
      .attr("d", function(d){
        let middle_x = (d.target.x - d.source.x) / 2 + d.source.x;
        let middle_y = (d.target.y - d.source.y) / 2 + d.source.y;
        let moveto = `M${d.source.x},${d.source.y}`;
        let lineto = `L${middle_x},${middle_y}L${d.target.x},${d.target.y}`;
        return `${moveto}${lineto}`;
      })
      .attr("id", (d) => `${d.source.id}_${d.target.id}`);
    // add new gedges,
    let newPs = gedges.enter().append("g");
    newPs.on("mouseup", function (d) {
        thisGraph.EdgeMouseUp.call(thisGraph, d3.select(this), d);
    });
    newPs
      .append("path")
      .style('marker-mid', 'url(#end-arrow)')
      .classed("link", true)
      .attr("d", function(d){
        let middle_x = (d.target.x - d.source.x) / 2 + d.source.x;
        let middle_y = (d.target.y - d.source.y) / 2 + d.source.y;
        let moveto = `M${d.source.x},${d.source.y}`;
        let lineto = `L${middle_x},${middle_y}L${d.target.x},${d.target.y}`;
        return `${moveto}${lineto}`;
      })
      .attr("id", function (d) {
          return String(d.source.id) + "_" + String(d.target.id);
      })
      .on("mousedown", function(d){
        thisGraph.pathMouseDown.call(thisGraph, d3.select(this), d);
        }
      )
      .on("mouseup", function(d){
        state.mouseDownLink = null;
      });

    // Display the good edge label according to the displayType
    newPs.each(function (d) {
      if (state.displayType == displayType.PROBABILITY){
        d.label_fwd = d.propagationProba_fwd
        d.label_bwd = d.propagationProba_bwd
      }
      else{
        d.label_fwd = d.propagationTime_fwd
        d.label_bwd = d.propagationTime_bwd
      }
      thisGraph.insertEdgeLabel(d3.select(this), d);
    });

    // remove old links
    gedges.exit().remove();

    gedges
      .style('stroke', function (d) {return d.color; })
      .attr("stroke-dasharray", function (d) {return consts.STROKES[d.stroke];});

    // update existing nodes
    thisGraph.gnodes = thisGraph.gnodes.data(thisGraph.nodes, function(d){ return d.id;});
    thisGraph.gnodes.attr("transform", function(d){return "translate(" + d.x + "," + d.y + ")";});

    // add new nodes
    let newGs= thisGraph.gnodes.enter().append("g");

    newGs.classed(consts.nodeGClass, true)
      .attr("transform", function(d){return "translate(" + d.x + "," + d.y + ")";})
      .on("mouseover", function(d){
        if (state.shiftNodeDrag){
          d3.select(this).classed(consts.connectClass, true);
        }
        d3.select('#node_info_window').transition()
            .duration(50)
            .style("opacity", 1);
        console.log(d3.select('#node_info_window'));
        let num = "555555555555555555555";
        d3.select('#node_info_window').html(num)
          .style("left", (d3.event.pageX + 40) + "px")
          .style("top", (d3.event.pageY - 15) + "px");

        d3.select('#node_info_window').text(num)
          .style("left", (d3.event.pageX + 40) + "px")
          .style("top", (d3.event.pageY - 15) + "px");
        console.log(d3.select('#node_info_window'));
        console.log("this");
        console.log(this);
        console.log(d3.select(this));
      })
      .on("mouseout", function(d){
        d3.select(this).classed(consts.connectClass, false);

          d3.select('#node_info_window').transition()
             .duration('50')
             .style("opacity", 0);
      })
      .on("mousedown", function(d){
        thisGraph.circleMouseDown.call(thisGraph, d3.select(this), d);
      })
      .on("mouseup", function(d){
        thisGraph.circleMouseUp.call(thisGraph, d3.select(this), d);
        // On mouseUp, update edge label orientation
        gedges = thisGraph.gedges
        gedges.each(
          function(d){
            let d3edge = d3.select(this);
            d3edge.selectAll("text").remove();
            thisGraph.insertEdgeLabel(d3edge, d);
          }
        );
       })
      .call(thisGraph.drag);

    let superform = d3.superformula()
        .type(formNodeMapping[nodeType.ASSET])
        .size(consts.nodeSize)
        .segments(360);

    newGs.append("path")
      .attr("class", "node")
      .attr("d", superform)
      .attr("width", String(consts.nodeSize))
      .attr("height", String(consts.nodeSize));

    newGs.each(function(d){
      thisGraph.insertTitleLinebreaks(d3.select(this), d);
    });

    // remove old nodes
    thisGraph.gnodes.exit().remove();

    thisGraph.gnodes.selectAll('.node')
      .style("stroke", "black")
      .attr("stroke-dasharray", function (d) {return consts.STROKES[d.stroke]; })
      .attr("stroke-width", "3px")
      //.style("fill", function (d) {return consts.COLORS[d.color][d.fint];})
      .style("fill", function (d) {return d.color;})
      .attr('d', superform.type(function(d) {return d.form;}))
      .attr('d', superform.size(function(d) {return d.size;}));
  };

  // Given a "g" (group) dom element --a node--, change the size of its rect element to fit the size of its text.
  GraphCreator.prototype.update_rectangle_size_based_on_text_size = function (g_dom_element) {
      let nodeMargin = this.consts.nodeMargin;
      d3.select(g_dom_element).selectAll('.node')
        .attr("width", function(d) { return d3.select(this.parentNode).select("text")[0][0].getBBox().width + nodeMargin*2; })
        .attr("height", function(d) { return d3.select(this.parentNode).select("text")[0][0].getBBox().height + nodeMargin*2; });
      d3.select(g_dom_element).selectAll('.node')
        .attr("x", function(d) { return -d3.select(this).attr('width')/2; })
        .attr("y", function(d) { return -d3.select(this).attr('height')/2; });
  };

  GraphCreator.prototype.zoomed = function(){
    this.state.justScaleTransGraph = true;
    d3.select("." + this.consts.graphClass)
      .attr("transform", "translate(" + this.dragSvg.translate() + ") scale(" + this.dragSvg.scale() + ")");
  };

  GraphCreator.prototype.updateWindow = function(svg){
    let docEl = document.documentElement,
        bodyEl = document.getElementsByTagName('body')[0];
    let x = window.innerWidth || docEl.clientWidth || bodyEl.clientWidth;
    let y = window.innerHeight|| docEl.clientHeight|| bodyEl.clientHeight;
    //Adjust with left Panel
    //x = document.getElementById('main_panel').clientWidth;
    x -= LEFTPANELSIZE;
    svg.attr("width", x).attr("height", y);
  };

  GraphCreator.prototype.addNode = function (d) {
    let thisGraph = this;
    thisGraph.nodes.push(d);
    thisGraph.undo_manager.add({
            undo: function () {
                thisGraph.deleteNodeAndItsEdges(d);
            },
            redo: function () {
                thisGraph.addNode(d);
            }
        });
  };

  GraphCreator.prototype.deleteNodeAndItsEdges = function (d) {
    let thisGraph = this;
    let nodeAt = thisGraph.nodes.indexOf(d);
    thisGraph.nodes.splice(nodeAt, 1);
    // remove edges associated with a node
    let edgesAt = [];
    let edgesToSplice = thisGraph.edges.filter(function(l) {
      return (l.source === d || l.target === d);
    });
    edgesToSplice.map(function(l) {
      let edgeAt = thisGraph.edges.indexOf(l);
      edgesAt.push(edgesAt);
      thisGraph.edges.splice(edgeAt, 1);
    });

    thisGraph.undo_manager.add({
            undo: function () {
                // reinsert the node at the same position
                thisGraph.nodes.splice(nodeAt, 0, d);
                // and its edges too
                edgesToSplice.map(function(l, idx) {
                    let edgeAt = edgesAt[idx];
                    thisGraph.edges.splice(edgeAt, 0, l);
                });
            },
            redo: function () {
                thisGraph.deleteNodeAndItsEdges(d);
            }
        });
  };

  GraphCreator.prototype.addEdge = function(e) {
    let thisGraph = this;
    thisGraph.edges.push(e);

    thisGraph.undo_manager.add({
            undo: function () {
                thisGraph.deleteEdge(e);
            },
            redo: function () {
                thisGraph.addEdge(e);
            }
        });
  };

  GraphCreator.prototype.deleteEdge = function (e) {
    let thisGraph = this;
    let edgeAt = thisGraph.edges.indexOf(e);
    thisGraph.edges.splice(edgeAt, 1);

    thisGraph.undo_manager.add({
            undo: function () {
                thisGraph.edges.splice(edgeAt, 0, e);
            },
            redo: function () {
                thisGraph.deleteEdge(e);
            }
        });
  };

  GraphCreator.prototype.changeDisplayType = function(){
    let thisGraph = this,
        state = thisGraph.state;
    if (state.displayType == displayType.PROBABILITY){
      state.displayType = displayType.TEMPORAL;
      // Change edges values
      thisGraph.gedges.each(function (d) {
          let d3edge = d3.select(this);
          d.label_fwd = d.propagationTime_fwd;
          d.label_bwd = d.propagationTime_bwd;
          //Apply changes
          d3edge.selectAll("text").remove();
          thisGraph.insertEdgeLabel(d3edge, d);
          });
      // Update displayed buttons
      d3.select('#button_temporal').property("checked", true);
      d3.select('#title_button_getImpact').text("Critical Time Computation");
      d3.select('#button_getImpact').text(getButtonText.TEMPORAL);
      d3.select('#button_getCriticality').property("disabled", true);
    }
    else {
      state.displayType = displayType.PROBABILITY;
      // Change edges values
      thisGraph.gedges.each(function (d) {
          let d3edge = d3.select(this);
          d.label_fwd = d.propagationProba_fwd;
          d.label_bwd = d.propagationProba_bwd;
          //Apply changes
          d3edge.selectAll("text").remove();
          thisGraph.insertEdgeLabel(d3edge, d);
      });
      // Update displayed buttons
      d3.select('#button_probability').property("checked", true);
      d3.select('#title_button_getImpact').text("Business Impact Computation");
      d3.select('#button_getImpact').text(getButtonText.PROBABILITY);
      d3.select('#button_getCriticality').property("disabled", false);
    }
  };

  let create_svg_helper = function create_svg_helper(el, width, height) {
      let docEl = document.documentElement,
          bodyEl = document.getElementsByTagName('body')[0];

      if (!width) {
          width = window.innerWidth || docEl.clientWidth || bodyEl.clientWidth;
      }

      if (!height) {
          height = window.innerHeight|| docEl.clientHeight|| bodyEl.clientHeight;
      }
      // Left Panel pixels adjustement
      width -= LEFTPANELSIZE;

      let svg = d3.select(el).append("svg")
        .attr("width", width)
        .attr("height", height);

      return svg;
  };

  let load_url_graph = function(thisGraph) {
    const queryString = window.location.search;
    console.log(queryString);
    let urlParams = new URLSearchParams(queryString);
    if (urlParams.has('request')){
      let request_timestamp = urlParams.get('request');
      console.log('Try to retrieve graph from request nb');
      get_request_graph_from_api(thisGraph, request_timestamp);
    } else {
      get_default_graph_from_api(thisGraph);
    }
  };

  let get_request_graph_from_api = function(thisGraph, request_timestamp){
    console.log("Send request to get timestamp graph from the Python BIA API");
    let data_to_send = "";
    let urlArgs = `request_timestamp=${request_timestamp}`;
    let biaBackendAddress = thisGraph.consts.biaBackendAddress;
    let service = thisGraph.consts.urlGetRequestGraph;
    let service_url = `${biaBackendAddress}/${service}?${urlArgs}`;
    console.log(service_url);
    $.ajax({
      type: 'post',
      url: service_url,
      async: true,
      dataType: "json",
      contentType: "application/json",
      data: data_to_send,
      success: function (response) {
        let json_graph = response
        console.log('Response from api');
        console.log(json_graph);
        thisGraph.load_graph_from_json(json_graph)
        thisGraph.centerGraph();
      }
    }).done(function (data) {
      console.log("Succeed");
    });
  };

  let get_default_graph_from_api = function(thisGraph){
    console.log("Send request to get default graph from the Python BIA API");
    let biaBackendAddress = thisGraph.consts.biaBackendAddress;
    let service = thisGraph.consts.urlGetDefaultGraph;
    let service_url = `${biaBackendAddress}/${service}`;
    console.log(service_url);
    $.ajax({
      type: 'get',
      url: service_url,
      async: true,
      success: function (response) {
        let json_graph = response
        console.log('Response from api');
        console.log(json_graph);
        thisGraph.load_graph_from_json(json_graph)
        thisGraph.centerGraph();
      }
    }).done(function (data) {
      console.log("Succeed");
    });
  };


  let load_help_graph = function (thisGraph) {
      //Default first graph
      let data_json = {"nodes":[
        {"id":29,"title":"__A__","uuid":"51","ip":"192.58.2.1","x":192.81753540039062,"y":205.31521606445312,"color":"#fbc246","form":"ellipse", "stroke":0, "fint":3,"type":"Asset","size":5000},
        {"id":30,"title":"__B__","uuid":"52","ip":"192.58.2.2","x":9.817535400390625,"y":289.3152160644531,"color":"#fbc246","form":"ellipse", "stroke":0, "fint":3,"type":"Asset","size":5000},
        {"id":31,"title":"__C__","uuid":"53","ip":"192.58.2.3","x":383.8175354003906,"y":295.3152160644531,"color":"#95cc00","form":"ellipse", "stroke":0, "fint":3,"type":"Asset","size":5000},
        {"id":32,"title":"__D__","uuid":"54","ip":"192.58.2.4","x":190.81753540039062,"y":377.3152160644531,"color":"#c91c1f","form":"ellipse", "stroke":0, "fint":3,"type":"Asset","size":5000},
        {"id":33,"title":"BF 2","x":-13.182464599609375,"y":130.31521606445312,"color":"#c91c1f","form":"rectangle", "stroke":0, "fint":3,"type":"Business","size":4000},
        {"id":34,"title":"BF 1","x":393.8175354003906,"y":134.31521606445312,"color":"#95cc00","form":"rectangle", "stroke":0, "fint":3,"type":"Business","size":4000},
        {"id":35,"title":"BP 1","x":196.81753540039062,"y":82.31522369384766,"color":"#fbc246","form":"rectangle", "stroke":0, "fint":3,"type":"Business","size":4000},
        {"id":36,"title":"SE B","x":-95.18246459960938,"y":431.3152160644531,"color":"white","form":"hexagon", "stroke":0, "fint":3,"type":"Shock","size":4000}],
        "edges":[{"source":31,"target":29,"propagationProba_fwd":0.4,"propagationProba_bwd":0.2,"propagationTime_fwd":0,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":32,"target":29,"propagationProba_fwd":0.8,"propagationProba_bwd":0.2,"propagationTime_fwd":0,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":32,"target":30,"propagationProba_fwd":0.9,"propagationProba_bwd":0.3,"propagationTime_fwd":0,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":30,"target":29,"propagationProba_fwd":0.4,"propagationProba_bwd":0.1,"propagationTime_fwd":0,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":34,"target":35,"propagationProba_fwd":0.8,"propagationProba_bwd":0,"propagationTime_fwd":1,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":33,"target":35,"propagationProba_fwd":0.42,"propagationProba_bwd":0,"propagationTime_fwd":2,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":29,"target":34,"propagationProba_fwd":0.7,"propagationProba_bwd":0,"propagationTime_fwd":2,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":29,"target":33,"propagationProba_fwd":0.5,"propagationProba_bwd":0,"propagationTime_fwd":3,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":30,"target":33,"propagationProba_fwd":0.9,"propagationProba_bwd":0,"propagationTime_fwd":2,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":32,"target":31,"propagationProba_fwd":0.7,"propagationProba_bwd":0.1,"propagationTime_fwd":0,"propagationTime_bwd":"","stroke":0, "color":"black"},
        {"source":36,"target":30,"propagationProba_fwd":0.8,"propagationProba_bwd":0,"propagationTime_fwd":0,"propagationTime_bwd":"","stroke":0, "color":"black"}]}
      let data = window.JSON.stringify(data_json, {type: "text/plain;charset=utf-8"});
      let json_graph = JSON.parse(data);
      thisGraph.load_graph_from_json(json_graph);
      thisGraph.centerGraph();
  };

  // Save a SVG as a PNG image
  // Based on http://bl.ocks.org/Rokotyan/0556f8facbaf344507cdc45dc3622177
  function save_svg_as_png_image(svg_node, width, height, save_cb) {
      svg_node.setAttribute('xlink', 'http://www.w3.org/1999/xlink');
      add_css_rules_into_svg(svg_node);
      let svg_url = svg_string_as_url(serialize_svg_node(svg_node));
      svg_url_as_image(svg_url, 2*width, 2*height, 'png', save_cb);
      return;

      // helper functions
      function serialize_svg_node(svgNode) {
          let serializer = new XMLSerializer();
          let svgString = serializer.serializeToString(svgNode);
          svgString = svgString.replace(/(\w+)?:?xlink=/g, 'xmlns:xlink='); // Fix root xlink without namespace
          svgString = svgString.replace(/NS\d+:href/g, 'xlink:href'); // Safari NS namespace fix
          return svgString;
      }

      function svg_string_as_url(svg_string) {
          return 'data:image/svg+xml;base64,'+ btoa(unescape(encodeURIComponent(svg_string)));
      }

      // Get the CSS rules of the web page and insert them into the svg node
      // If the CSS rules are local (file://) this will not work on Chrome:
      //    - https://bugs.chromium.org/p/chromium/issues/detail?id=143626
      //    - https://bugs.chromium.org/p/chromium/issues/detail?id=490
      //
      // A workaround is to open Chrome with --allow-file-access-from-files flag
      function add_css_rules_into_svg(svg_node) {
          let extractedCSSText = "";
          for (let i = 0; i < document.styleSheets.length; i++) {
              let s = document.styleSheets[i];
              try {
                  if(!s.cssRules)
                      continue;
              } catch( e ) {
                  if(e.name !== 'SecurityError') throw e; // for Firefox
                  continue;
              }
              let cssRules = s.cssRules;
              for (let r = 0; r < cssRules.length; r++) {
                  extractedCSSText += cssRules[r].cssText;
              }
          }

          let styleElement = document.createElement("style");
          styleElement.setAttribute("type","text/css");
          styleElement.innerHTML = extractedCSSText;
          let refNode = svg_node.hasChildNodes() ? svg_node.children[0] : null;
          svg_node.insertBefore( styleElement, refNode );
      }

      function svg_url_as_image(svg_as_url, width, height, format, callback) {
          let canvas = document.createElement("canvas");
          let context = canvas.getContext("2d");
          canvas.width = width;
          canvas.height = height;
          let image = new Image();
          image.onload = function() {
              context.clearRect ( 0, 0, width, height );
              context.drawImage(image, 0, 0, width, height);
              canvas.toBlob( function(blob) {
                  let filesize = Math.round( blob.length/1024 ) + ' KB';
                  if ( callback ) callback( blob, filesize );
              });
          };
          image.src = svg_as_url;
      }
  }
  // export
  window.GraphCreator = GraphCreator;
  window.create_svg_helper = create_svg_helper;
  window.load_help_graph = load_url_graph;
  window.load_url_graph = load_url_graph;

})(window.d3, window.saveAs, window.Blob, window.UndoManager, window.alertify);
