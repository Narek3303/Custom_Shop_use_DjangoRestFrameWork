document.addEventListener('DOMContentLoaded', function() {
    const productSelect = document.getElementById('id_product');
    const sizeSelect = document.getElementById('id_size');
    const imagesContainer = document.getElementById('product-images-container');

    // When product changes, fetch sizes and images
    if (productSelect) {
        productSelect.addEventListener('change', function() {
            const productId = this.value;
            if (productId) {
                fetch(`/admin/shop/sizeprice/api/product/${productId}/sizes/`)
                    .then(response => response.json())
                    .then(data => {
                        // Update size options
                        if (sizeSelect) {
                            sizeSelect.innerHTML = '';  // Clear existing options
                            data.sizes.forEach(size => {
                                const option = new Option(size.name, size.id);
                                sizeSelect.add(option);
                            });
                        }

                        // Update product images
                        if (imagesContainer) {
                            imagesContainer.innerHTML = '';  // Clear existing images
                            data.images.forEach(imageUrl => {
                                const imgElement = document.createElement('img');
                                imgElement.src = imageUrl;
                                imgElement.alt = 'Product Image';
                                imgElement.style.width = '80px';
                                imgElement.style.height = '80px';
                                imgElement.style.marginRight = '10px';
                                imagesContainer.appendChild(imgElement);
                            });
                        }
                    })
                    .catch(error => {
                        console.error('There was a problem with the fetch operation:', error);
                    });
            } else {
                sizeSelect.innerHTML = '<option value="">---------</option>';
            }
        });

        // Trigger change event if a product is pre-selected
        if (productSelect.value) {
            productSelect.dispatchEvent(new Event('change'));
        }
    }
});
