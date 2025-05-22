;(function($) {
  $(document).ready(function() {
    // 1. Insert "Show Discounts" toggle button
    const $btnContainer = $('<div id="changelist-filter-buttons"></div>');
    const $toggleBtn = $('<button type="button">Show Only Discounts</button>');
    $btnContainer.append($toggleBtn);
    $('.change-list').find('.breadcrumbs').after($btnContainer);

    let showingDiscounts = false;
    $toggleBtn.on('click', function() {
      showingDiscounts = !showingDiscounts;
      if (showingDiscounts) {
        $('tr').has('td.field-discount_info span').show();
        $('tr').not(':has(td.field-discount_info span)').hide();
        $toggleBtn.text('Show All Items');
      } else {
        $('tr').show();
        $toggleBtn.text('Show Only Discounts');
      }
    });

    // 2. Expandable price difference detail
    $('td.field-price_difference').each(function() {
      const $cell = $(this);
      const shortText = $cell.text();
      const fullValue = $cell.data('full-diff');  // we’ll inject this in Django
      if (fullValue) {
        $cell.css('cursor', 'pointer');
        $cell.attr('title', 'Click to see full difference');
        $cell.on('click', function() {
          alert('Price difference: ' + fullValue + ' AMD');
        });
      }
    });
  });
})(django.jQuery);
