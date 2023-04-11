//==============================================================================
// POPUP
//==============================================================================

let StackTracePopup = function() {
    this.isShowing = false;
    this.displayTimer = false;
    this.displayTimeout = 500;

    this.initEvents();
}

StackTracePopup.prototype.initEvents = function() {
    const self = this;

    $(".trace-popup").hover(function() {
        if (self.displayTimer) {
            clearTimeout(self.displayTimer);
        }
    }, function () {
        self.hide();
    });
}

StackTracePopup.prototype.show = function(trace, top, left) {
    $(".trace-popup")
        .html("<pre>" + trace + "</pre>")
        .css({ top: top + "px", left: left + "px"})
        .show();
    this.isShowing = true;
}

StackTracePopup.prototype.hide = function() {
    const self = this;
    this.displayTimer = setTimeout(function() {
        self.hideNow();
    }, this.displayTimeout);
}

StackTracePopup.prototype.hideNow = function() {
    $(".trace-popup").hide();
    this.isShowing = false;
}

//==============================================================================
// TABLE
//==============================================================================

let StackTraceTable = function() {
    this.selected_cell = false;
    this.popup = new StackTracePopup();
    this.mouseX = 0;
    this.mouseY = 0;

    this.initEvents();
}

StackTraceTable.prototype.initEvents = function() {
    const self = this;

    $(".data-table").on("click", ".cell", function() {
        let key = $(this).data('key');
        self.clearSelected();
        self.highlightCell($(this));
        self.show_stack_trace(key, self.mouseY, self.mouseX);
    });

    $(document).bind("mousemove", function(e) {
        self.mouseX = e.pageX;
        self.mouseY = e.pageY;
    });

    $(document).bind("keyup", function(e) {
        if (self.popup.isShowing) {
            if (e.key == "Escape") {
                self.popup.hideNow();
                return;
            }
        }
    });
}

StackTraceTable.prototype.removeHighlights = function() {
    $(".data-table .cell.highlight").removeClass("highlight");
}

StackTraceTable.prototype.clearSelected = function() {
    this.selected_cell = false;
    this.removeHighlights();
}

StackTraceTable.prototype.highlightCell = function(td) {
    this.selected_cell = td;
    td.addClass("highlight");
}

StackTraceTable.prototype.show_stack_trace = function(key, top, left) {
    if (typeof STACK_TRACES === "undefined")
        return;

    let trace = STACK_TRACES[key];
    this.popup.show(trace, top, left);
}

$(function() {
    const stackTraceTable = new StackTraceTable();
});
