// admin/js/sizeprice_admin.js
(function($) {
  $(document).ready(function() {
    // 1) Inline edit price-ը բարելավել
    $('td.field-price').each(function() {
      var $cell = $(this);
      var priceText = $cell.text().trim();
      $cell.html(
        '<input type="number" step="0.01" class="inline-price-input" value="' +
          priceText.replace(/\,/g, '') +
          '" style="width: 80px;" />'
      );
    });

    // 2) Պահուստավոր ստուգում նոր արժեքի մուտքագրելիս
    $('.inline-price-input').on('change', function() {
      var val = parseFloat(this.value);
      if (val < 0) {
        alert('Գինը չի կարող բացասական լինել։');
        this.value = Math.abs(val);
      }
    });

    // 3) Առավելագույն արժեքի թուլ առաջադրանք
    $('.inline-price-input').on('blur', function() {
      var val = parseFloat(this.value);
      if (val > 50000) {
        $(this).css('border', '2px solid #c00');
        $(this).attr('title', 'Գինը շատ բարձր է՝ հաստատե՞լ եք');
      } else {
        $(this).css('border', '');
        $(this).removeAttr('title');
      }
    });
  });
})(django.jQuery);
