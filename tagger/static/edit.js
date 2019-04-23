var socket = io.connect('http://' + document.domain + ':' + location.port);
var bbs, explanation_candidates;
var current_phrase_i = 0, current_candidate_j = 0;
var explanation_labels;
var token_map;    

function requestRender () {
    let sidebar = document.getElementById('slide-out');
    
    let cur_time = new Date().getTime();
    let list_elem = document.createElement("li");
    list_elem.dataset.timestamp = cur_time;
    let a_elem = document.createElement("a");
    a_elem.className = "truncate";
    let font_elem = document.createElement("font");
    font_elem.size = -1;
    font_elem.textContent = "Sending request...";
    let progress_elem = document.createElement("div");
    progress_elem.className = "progress";
    let inner_prog_elem = document.createElement("div");
    inner_prog_elem.className = "indeterminate";
    
    progress_elem.appendChild(inner_prog_elem);
    a_elem.appendChild(font_elem);
    list_elem.appendChild(a_elem);
    list_elem.appendChild(progress_elem);
    sidebar.appendChild(list_elem);
    
    socket.emit('request new paper', {
        email: user_email,
        timestamp: cur_time
    });
}
    
socket.on("render started", function (msg) {
    let list_elem = document.querySelector(`li[data-timestamp='${msg.timestamp}']`);
    list_elem.dataset.ssid = msg.ssid;
    list_elem.dataset.title = msg.title;
    list_elem.querySelector("font").textContent = "Rendering...";
});
    
socket.on("render finished", function (msg) {
    let list_elem = document.querySelector(`li[data-ssid='${msg.ssid}']`);
    list_elem.querySelector("font").textContent = list_elem.dataset.title;
    list_elem.querySelector(".progress").remove();
    list_elem.querySelector("a").href = msg.ssid;
});
    
$.getJSON('../edit_list', function(data) {
    let sidebar = document.getElementById('slide-out');
    for (let group of data.papers) {
        let list_elem = document.createElement("li");
        let a_elem = document.createElement("a");
        a_elem.className = "truncate";
        a_elem.href = group.ssid;
        let font_elem = document.createElement("font");
        font_elem.size = -1;
        font_elem.textContent = group.title;

        a_elem.appendChild(font_elem);
        list_elem.appendChild(a_elem);
        sidebar.appendChild(list_elem);
    }
});
    
$('.tagger-sidenav').click(function() {
    $('.sidenav').sidenav('open');
});
    
var img_container = document.getElementById("image-container");
var img_i;
for (img_i = 1; img_i <= number_of_images; img_i++) {
    var div_block = document.createElement("div");
    div_block.className = "document-container";
    
    var img_block = document.createElement("img");
    img_block.src = "../tagimgs/" + ssid + "/" + img_i;
    img_block.className = "responsive-img";
    img_block.dataset.taggingImagePage = img_i;
    
    var internal_div = document.createElement("div");
    var svg_block = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    internal_div.className = "document-overlay";
    internal_div.appendChild(svg_block);
 
    
    div_block.appendChild(img_block);
    div_block.appendChild(internal_div);
    img_container.appendChild(div_block);
}

function redraw_overlay () {
    $('.paragraph-bb').remove();
    $('.sentence-bb').remove();
    $('.target-bb').remove();
    svgs = d3.selectAll('.document-overlay').select('svg');
    // svgs.attr('width', svgs.parentNode.width);
    
    svgs = d3.selectAll('svg');
    dimensions = new Array(number_of_images + 1);
    svgs.each(function(d, i) {
        let image = this.parentNode.parentNode.childNodes[0];
        let width = image.offsetWidth;
        let height = image.offsetHeight
        this.setAttribute("width", width);
        this.setAttribute("height", height);
        dimensions[i + 1] = [width, height];
    });
    let paragraph_bbs = bbs.paragraphs;
    let sentence_bbs = bbs.sentences;
    let target_bbs = bbs.target_bbs;
    let pbbs_page_groups = [...Array(number_of_images)].map(e => []);
    let sbbs_page_groups = [...Array(number_of_images)].map(e => []);
    let tbbs_page_groups = [...Array(number_of_images)].map(e => []);
    
    function create_adjusted_bb(page_groups, bb) {
        // We adjust the paragraph bounding boxes to be a little taller so that
        // there aren't gaps
        let dimension = dimensions[bb.page];
        bb.x_adj = bb.x * dimension[0];
        bb.y_adj = (1 - bb.y - (bb.height * 1.1)) * dimension[1];
        bb.width_adj = bb.width * dimension[0];
        bb.height_adj = 1.1 * bb.height * dimension[1];
        page_groups[bb.page - 1].push(bb);
    }
    
    for (let p_bb of paragraph_bbs) {
        create_adjusted_bb(pbbs_page_groups, p_bb);
    }
    for (let s_bb of sentence_bbs) {
        create_adjusted_bb(sbbs_page_groups, s_bb);
    }
    
    for (let i = 0; i < target_bbs.length; i++) {
        for (let j = 0; j < target_bbs[i].length; j++) {
            for (let target of target_bbs[i][j]) {
                for (let t_bb of target) {
                    t_bb.target_group = i;
                    t_bb.within_group_index = j;
                    create_adjusted_bb(tbbs_page_groups, t_bb);
                }
            }
        }
    }
    
    function style_rects(rects) {
        let created_rects = rects.enter().append("rect");
        
        return created_rects.style("opacity", 0.0)
            .attr("x", function (d) { return d.x_adj; })
            .attr("y", function (d) { return d.y_adj; })
            .attr("width", function (d) { return d.width_adj; })
            .attr("height", function (d) { return d.height_adj; })
            ;
    }
    
    var p_rects = svgs.data(pbbs_page_groups)
                    .selectAll("rect").data(function(d) {return d;});
    p_rects = style_rects(p_rects).classed("paragraph-bb", true);
    
    var s_rects = svgs.data(sbbs_page_groups)
                    .selectAll("rect:not(.paragraph-bb)").data(function(d) {return d;});
    s_rects = style_rects(s_rects)
        .attr("fill", "green")
        .on("mouseover", sentenceMouseOver)
        .on("mouseout", sentenceMouseOut)
        .classed("sentence-bb", true)
        ;
    
    var t_rects = svgs.data(tbbs_page_groups)
                    .selectAll("rect:not(.paragraph-bb):not(.sentence-bb)").data(function(d) {return d;});
    t_rects = style_rects(t_rects)
        .style("opacity", function(d) {
                if (d.target_group == current_phrase_i) {
                    if (d.within_group_index == current_candidate_j) {
                        return 0.4;
                    }
                    return 0.15;
                }
                return 0.0;
            })
        .attr("fill", function(d) {
                if (explanation_labels[d.target_group][d.within_group_index] == 0) {
                    return "red";
                } else if (explanation_labels[d.target_group][d.within_group_index]) {
                    return "green";
                }
                return "blue";
            })
        .classed("target-bb", true)
        .attr("data-token-id", function(d) { return d.token_id; })
        ;
    
    function sentenceMouseOver (d, i) {
        s_rects.filter(function(d_inner) { return d_inner.sentence_id == d.sentence_id; })
            .transition().duration(.3).style("opacity", 0.2);
        p_rects.filter(function(d_inner) { return d_inner.paragraph_id == d.parent_id; })
            .transition().duration(.3).style("opacity", 0.12);
    }

    function sentenceMouseOut (d, i) {
        s_rects.filter(function(d_inner) { return d_inner.sentence_id == d.sentence_id; })
            .transition().style("opacity", 0.0);
        p_rects.filter(function(d_inner) { return d_inner.paragraph_id == d.parent_id; })
            .transition().style("opacity", 0.0);
    }
}
    
function scroll_and_highlight_candidate () {
    $('.target-bb').css('opacity', 0.0);
    let candidates = explanation_candidates[current_phrase_i]
    for (let j = 0; j < candidates.length; j++) {
        for (let k = 0; k < candidates[j].length; k++) {
            let token_id = candidates[j][k];
            let token_elems = $('*[data-token-id="' + token_id + '"]');
            if (j == current_candidate_j) {
                token_elems.css('opacity', 0.4);
                if (k == 0) {
                    let offset = token_elems.first().offset().top - $(window).height() / 2;
                    $('html, body').stop(true, false);
                    $('html, body').animate({scrollTop: offset}, 150);
                }
            } else {
                token_elems.css('opacity', 0.15);
            }
        }
    }
}
    
function update_info_text () {
    $("#phrase-counter").text("Phrase " + (current_phrase_i + 1) + "/" + explanation_candidates.length);
    $("#candidate-counter").text("Candidate " + (current_candidate_j + 1) + "/" + explanation_candidates[current_phrase_i].length);
}
    
function increment_candidate () {
    if (explanation_candidates[current_phrase_i].length > current_candidate_j + 1) {
        current_candidate_j++;
    } else if (explanation_candidates.length > current_phrase_i + 1) {
        current_phrase_i++;
        current_candidate_j = 0;
    } else {
        return;
    }
    update_info_text();
    scroll_and_highlight_candidate();
}
    
function decrement_candidate () {
    if (current_candidate_j > 0) {
        current_candidate_j--;
    } else if (current_phrase_i > 0) {
        current_phrase_i--;
        current_candidate_j = explanation_candidates[current_phrase_i].length - 1;
    } else {
        return;
    }
    update_info_text();
    scroll_and_highlight_candidate();
}
    
function set_candidate_score (score) {
    explanation_labels[current_phrase_i][current_candidate_j] = score;
    for (let candidate of explanation_candidates[current_phrase_i][current_candidate_j]) {
        $('*[data-token-id="' + candidate + '"]').css('fill', 'green');
    }
    
    // Need to make any "invalid" labels valid again
    for (let j = 0; j < explanation_candidates[current_phrase_i].length; j++) {
        if (explanation_labels[current_phrase_i][j] == 0) {
            explanation_labels[current_phrase_i][j] = null;
            for (let candidate of explanation_candidates[current_phrase_i][j]) {
                $('*[data-token-id="' + candidate + '"]').css('fill', 'blue');
            }
        }
    }
}
    
function set_candidate_invalid () {
    for (let j = 0; j < explanation_labels[current_phrase_i].length; j++) {
        explanation_labels[current_phrase_i][j] = 0;
    }
    current_candidate_j = explanation_labels[current_phrase_i].length - 1;
    
    for (let candidate_group of explanation_candidates[current_phrase_i]) {
        for (let candidate of candidate_group) {
            $('*[data-token-id="' + candidate + '"]').css('fill', 'red');
        }
    }
    
    increment_candidate();
}
    
$.getJSON('../tagdata/' + ssid, function(data) {
    bbs = data.bbs;
    explanation_candidates = data.explanation_candidates;
    explanation_labels = explanation_candidates.map(e => new Array(e.length));
    token_map = {};
    for (let token of bbs.tokens) {
        if (!(token.token_id in token_map)) {
            token_map[token.token_id] = [];
        }
        token_map[token.token_id].push(token); 
    }
    bbs.target_bbs = explanation_candidates.map(function(ec) {
        return ec.map(function(candidate_list) {
            return candidate_list.map(candidate => token_map[candidate]);
        });
    }); 
    
    redraw_overlay();
    scroll_and_highlight_candidate();
    update_info_text();
});
window.addEventListener("resize", redraw_overlay);
    
window.addEventListener('keydown', (e) => {
    if (e.key == "ArrowLeft") {
        decrement_candidate();
    } else if (e.key == "ArrowRight") {
        increment_candidate();
    } else if (e.code == "Digit1") {
        set_candidate_score(1);
    } else if (e.code == "Digit2") {
        set_candidate_score(2);
    } else if (e.code == "Digit3") {
        set_candidate_score(3);
    } else if (e.code == "KeyQ") {
        set_candidate_invalid();
    } else if (e.code == "KeyEnter") {
        // should submit the data?
    }
    // console.log(e);
});
    