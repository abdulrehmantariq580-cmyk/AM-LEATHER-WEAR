import csv
import urllib.request
import re
import os

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROGl1b8ZoEhh8yOk-LLvqFPKJKm7dqRiAmQfBbBqYCq9Aae5igtLzk8u-Oi60JSBkYtEo926M-trS2/pub?output=csv"

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text

def convert_drive_link(url, size='w1000'):
    if not url: return ''
    if 'drive.google.com' in url or 'googleusercontent.com' in url:
        match = re.search(r'id=([^&]+)', url) or re.search(r'/d/([^/]+)', url)
        if match:
            return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz={size}"
    return url

def main():
    print("Fetching CSV from Google Sheets...")
    req = urllib.request.Request(CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    lines = [l.decode('utf-8') for l in response.readlines()]
    
    # Strip spaces from headers
    reader = csv.reader(lines)
    headers = [h.strip() for h in next(reader)]
    dict_reader = csv.DictReader(lines[1:], fieldnames=headers)
    
    products = [row for row in dict_reader if row.get('Product Title', '').strip()]

    print("Reading index.html for UI components...")
    with open('index.html', 'r', encoding='utf-8') as f:
        index_html = f.read()

    # Extract components using regex
    head_match = re.search(r'(<!DOCTYPE html>.*?<style>.*?</style>)', index_html, re.DOTALL)
    head_content = head_match.group(1) if head_match else ""

    top_ui_match = re.search(r'(<!-- ================= ANNOUNCEMENT BAR ================= -->.*?<!-- ================= HERO SLIDER ================= -->)', index_html, re.DOTALL)
    top_ui = top_ui_match.group(1).replace('<!-- ================= HERO SLIDER ================= -->', '') if top_ui_match else ""

    footer_match = re.search(r'(<!-- ================= FOOTER ================= -->.*?</footer>)', index_html, re.DOTALL)
    footer = footer_match.group(1) if footer_match else ""
    
    base_js = """
    <!-- ================= CONSOLIDATED JAVASCRIPT ================= -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>
    <script>
        const SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROGl1b8ZoEhh8yOk-LLvqFPKJKm7dqRiAmQfBbBqYCq9Aae5igtLzk8u-Oi60JSBkYtEo926M-trS2/pub?output=csv";
        let cartArray = JSON.parse(localStorage.getItem('am_cart')) || [];
        
        // This will hold the live data once fetched
        let liveProductData = null;

        document.addEventListener("DOMContentLoaded", () => {
            updateCartUI();
        });

        const overlay = document.getElementById('overlay');
        const mobileMenu = document.getElementById('mobileMenu');
        const cartDrawer = document.getElementById('cartDrawer');

        function toggleMenu() { mobileMenu.classList.toggle('active'); overlay.classList.toggle('active'); cartDrawer.classList.remove('active'); }
        function toggleCart() { cartDrawer.classList.toggle('active'); overlay.classList.toggle('active'); mobileMenu.classList.remove('active'); }
        function closeDrawers() { mobileMenu.classList.remove('active'); cartDrawer.classList.remove('active'); overlay.classList.remove('active'); }
        function toggleMobileDropdown() { const parent = document.querySelector('.has-dropdown'); if (parent) parent.classList.toggle('open'); }
        function openSearch() { document.getElementById('searchOverlay').classList.add('active'); document.body.style.overflow = 'hidden'; setTimeout(() => document.getElementById('searchInput').focus(), 100); }
        function closeSearch() { document.getElementById('searchOverlay').classList.remove('active'); document.body.style.overflow = ''; }
        function clearSearch() { document.getElementById('searchInput').value = ''; document.getElementById('clearSearchBtn').style.display = 'none'; document.getElementById('searchInput').focus(); }
        function proceedToCheckout() {
            if (cartArray.length === 0) { alert('Your bag is empty!'); return; }
            window.location.href = '../checkout.html';
        }

        function changeQuantity(cartIndex, amount) {
            cartArray[cartIndex].quantity += amount;
            if(cartArray[cartIndex].quantity <= 0) { cartArray.splice(cartIndex, 1); }
            localStorage.setItem('am_cart', JSON.stringify(cartArray));
            updateCartUI();
        }
        function removeFromCart(cartIndex) {
            cartArray.splice(cartIndex, 1);
            localStorage.setItem('am_cart', JSON.stringify(cartArray));
            updateCartUI();
        }
        function updateCartUI() {
            const container = document.getElementById('cartItemsContainer');
            const counters = document.querySelectorAll('.cart-count');
            const subtotalText = document.getElementById('cartSubtotal');
            const totalCount = cartArray.reduce((sum, item) => sum + item.quantity, 0);
            counters.forEach(c => c.innerText = totalCount);
            if(!container) return;
            if(cartArray.length === 0) {
                container.innerHTML = `<p style="color: var(--accent); font-size: 14px; text-transform: uppercase; text-align: center; margin-top: 40px;">Your bag is empty.</p>`;
                if(subtotalText) subtotalText.innerText = `Rs. 0`;
                return;
            }
            let html = '';
            let total = 0;
            cartArray.forEach((item, idx) => {
                total += (item.price * item.quantity);
                
                let finalImg = item.image;
                if (finalImg && finalImg.startsWith('../')) finalImg = finalImg.substring(3);
                if (finalImg && !finalImg.startsWith('http') && window.location.pathname.includes('/products/')) {
                    finalImg = '../' + finalImg;
                }

                html += `
                    <div class="cart-item">
                        <img src="${finalImg}" alt="${item.title}">
                        <div class="cart-item-details">
                            <div class="cart-item-title">${item.title}</div>
                            <div class="cart-item-price">Rs. ${item.price} x ${item.quantity}</div>
                            <div class="cart-quantity-controls">
                                <button class="qty-btn" onclick="changeQuantity(${idx}, -1)">-</button>
                                <span class="cart-item-qty">${item.quantity}</span>
                                <button class="qty-btn" onclick="changeQuantity(${idx}, 1)">+</button>
                            </div>
                        </div>
                        <button class="remove-item-btn" onclick="removeFromCart(${idx})" title="Remove item"><i class="fas fa-trash-alt"></i></button>
                    </div>
                `;
            });
            container.innerHTML = html;
            if(subtotalText) subtotalText.innerText = `Rs. ${total.toLocaleString()}`;
        }
        
        function addToCart(fallbackTitle, fallbackPrice, fallbackImage, fallbackShipping) {
            // Use live data if available, otherwise use fallback hardcoded data
            const title = liveProductData ? liveProductData.title : fallbackTitle;
            const price = parseFloat(liveProductData ? liveProductData.price : fallbackPrice) || 0;
            const image = liveProductData ? liveProductData.image : fallbackImage;
            let shipping = liveProductData ? liveProductData.shipping : fallbackShipping;
            
            shipping = parseFloat(shipping) || 0;

            const existingItem = cartArray.find(item => item.title === title);
            if(existingItem) {
                existingItem.quantity += 1;
            } else {
                cartArray.push({ title, price, image, shipping, quantity: 1 });
            }
            localStorage.setItem('am_cart', JSON.stringify(cartArray));
            updateCartUI();
            
            // Show toast
            const existingToast = document.querySelector('.custom-toast');
            if(existingToast) existingToast.remove();
            const toast = document.createElement('div');
            toast.className = 'custom-toast';
            toast.innerText = 'Added to Cart!';
            Object.assign(toast.style, {
                position: 'fixed', bottom: '30px', right: '5%', backgroundColor: 'var(--brand-dark)', color: 'var(--white)',
                padding: '15px 30px', borderRadius: '4px', fontFamily: "'Montserrat', sans-serif", fontSize: '14px',
                fontWeight: '600', boxShadow: '0 10px 30px rgba(0,0,0,0.2)', zIndex: '10000', opacity: '0',
                transform: 'translateY(20px)', transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
            });
            document.body.appendChild(toast);
            setTimeout(() => { toast.style.opacity = '1'; toast.style.transform = 'translateY(0)'; }, 10);
            setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateY(20px)'; setTimeout(() => toast.remove(), 300); }, 3000); 
            
            toggleCart();
        }

        // --- Drive Link Converter ---
        function convertDriveLinkJS(url, size = 'w1000') {
            if (!url) return '';
            if (url.includes('drive.google.com') || url.includes('googleusercontent.com')) {
                const idMatch = url.match(/id=([^&]+)/) || url.match(new RegExp('/d/([^/]+)'));
                if (idMatch && idMatch[1]) {
                    return `https://drive.google.com/thumbnail?id=${idMatch[1]}&sz=${size}`;
                }
            }
            return url; 
        }
    </script>
</body>
</html>
"""

    # Adjust Top UI Links for subdirectory 'products/'
    top_ui = top_ui.replace('href="index.html"', 'href="../index.html"')
    top_ui = top_ui.replace('href="shop.html', 'href="../shop.html')
    top_ui = top_ui.replace('src="media/', 'src="../media/')
    
    footer = footer.replace('href="index.html"', 'href="../index.html"')
    footer = footer.replace('href="shop.html', 'href="../shop.html')

    product_css = """
    <style>
        /* Product Page Styles */
        .product-page {
            max-width: 1200px;
            margin: 60px auto 100px;
            padding: 0 5%;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            align-items: start;
            min-height: 50vh;
        }
        .product-gallery {
            background: #f7f7f7;
            padding: 40px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #eee;
        }
        .product-gallery img {
            max-width: 100%;
            height: auto;
            max-height: 550px;
            object-fit: contain;
            transition: opacity 0.3s ease;
        }
        .product-details {
            display: flex;
            flex-direction: column;
        }
        .breadcrumb {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 20px;
        }
        .breadcrumb a { color: var(--brand-dark); font-weight: 600; }
        .product-title {
            font-family: 'Oswald', sans-serif;
            font-size: 42px;
            line-height: 1.2;
            color: var(--brand-dark);
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        .product-price {
            font-size: 26px;
            font-weight: 700;
            color: var(--brand-dark);
            margin-bottom: 25px;
        }
        .product-desc {
            font-size: 15px;
            line-height: 1.8;
            color: #555;
            margin-bottom: 35px;
        }
        .product-meta {
            border-top: 1px solid #eee;
            padding-top: 25px;
            margin-bottom: 35px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }
        .meta-item h4 {
            font-size: 13px;
            text-transform: uppercase;
            color: #111;
            margin-bottom: 5px;
            font-weight: 700;
        }
        .meta-item p {
            font-size: 14px;
            color: #666;
        }
        .add-to-cart-btn {
            background: var(--brand-dark);
            color: var(--white);
            border: none;
            padding: 18px;
            font-size: 15px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-bottom: 15px;
        }
        .add-to-cart-btn:hover {
            background: #444;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .whatsapp-share-btn {
            background: #25d366;
            color: #fff;
            border: none;
            padding: 15px;
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .whatsapp-share-btn:hover {
            background: #1ebc57;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(37, 211, 102, 0.3);
        }
        
        @media (max-width: 992px) {
            .product-page { grid-template-columns: 1fr; gap: 40px; margin: 40px auto; }
            .product-title { font-size: 32px; }
            .product-meta { grid-template-columns: 1fr; gap: 15px; }
        }
    </style>
    """
    
    os.makedirs('products', exist_ok=True)
    
    for product in products:
        title = product.get('Product Title', 'Product')
        price = product.get('Regular Price (Rs.)', '0')
        desc = product.get('Product Description', 'Premium leather product.')
        cat = product.get('Product Category', product.get('Category', 'Leather'))
        sizes = product.get('Sizes Available (Comma Separated)', product.get('Available Sizes', 'Standard'))
        material = product.get('Material Type', '100% Genuine Leather')
        delivery = product.get('Shipping Fee (Rs.)', 'Free Across Pakistan')
        raw_image = product.get('Main Product Image  (Only 1)', '')
        
        image_url = convert_drive_link(raw_image, 'w1000')
        if not image_url.startswith('http'):
            image_url = '../' + image_url
            
        slug = slugify(title)
        if not slug: continue
        
        og_tags = f"""
    <!-- Open Graph for WhatsApp & Facebook -->
    <meta property="og:title" content="{title} | A.M LEATHER WEAR">
    <meta property="og:description" content="{desc[:150]}...">
    <meta property="og:image" content="{image_url}">
    <meta property="og:type" content="product">
    <title>{title} | A.M LEATHER WEAR</title>
        """
        
        custom_head = head_content.replace('<title>A.M LEATHER WEAR | Premium Store</title>', og_tags)
        custom_head += product_css
        
        page_html = f"""
        <main class="product-page">
            <div class="product-gallery">
                <img id="liveMainImage" src="{image_url}" alt="{title}">
            </div>
            <div class="product-details">
                <div class="breadcrumb">
                    <a href="../index.html">Home</a> / <a href="../shop.html?category={cat}"><span id="liveCategory">{cat}</span></a> / {title}
                </div>
                <h1 class="product-title" id="liveTitle">{title}</h1>
                <div class="product-price" id="livePrice">Rs. {price}</div>
                <p class="product-desc" id="liveDesc">{desc}</p>
                
                <div class="product-meta">
                    <div class="meta-item">
                        <h4>Material</h4>
                        <p id="liveMaterial">{material}</p>
                    </div>
                    <div class="meta-item">
                        <h4>Sizes Available</h4>
                        <p id="liveSizes">{sizes}</p>
                    </div>
                    <div class="meta-item">
                        <h4>Category</h4>
                        <p>{cat}</p>
                    </div>
                    <div class="meta-item">
                        <h4>Delivery Charges</h4>
                        <p id="liveDelivery">Rs. {delivery}</p>
                    </div>
                </div>
                
                <button class="add-to-cart-btn" onclick="addToCart('{title}', '{price}', '{image_url}', '{delivery}')">Add to Cart</button>
                
                <button class="whatsapp-share-btn" onclick="window.open('https://wa.me/?text=Check out this premium ' + encodeURIComponent(document.getElementById('liveTitle').innerText) + ' from A.M LEATHER WEAR: ' + encodeURIComponent(window.location.href), '_blank')">
                    <i class="fab fa-whatsapp"></i> Share on WhatsApp
                </button>
            </div>
        </main>
        
        <!-- Live Hydration Script: Fetches latest data from Google Sheets instantly -->
        <script>
            document.addEventListener("DOMContentLoaded", () => {{
                // Bypass Google Sheet Cache with a unique timestamp
                const cacheBusterUrl = SHEET_CSV_URL + "&t=" + new Date().getTime();
                
                Papa.parse(cacheBusterUrl, {{
                    download: true,
                    header: true,
                    skipEmptyLines: true,
                    transformHeader: function(header) {{ return header.trim(); }},
                    complete: function(results) {{
                        const currentSlug = "{slug}";
                        
                        const liveProduct = results.data.find(p => {{
                            const pTitle = p['Product Title'] || '';
                            const pSlug = pTitle.toString().toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/[\s-]+/g, '-');
                            return pSlug === currentSlug;
                        }});
                        
                        if (liveProduct) {{
                            const lTitle = liveProduct['Product Title'];
                            const lPrice = liveProduct['Regular Price (Rs.)'];
                            const lDesc = liveProduct['Product Description'];
                            const lSizes = liveProduct['Sizes Available (Comma Separated)'] || liveProduct['Available Sizes'] || 'Standard';
                            const lCat = liveProduct['Product Category'] || liveProduct['Category'] || 'Leather Goods';
                            const lMat = liveProduct['Material Type'] || '100% Genuine Leather';
                            const lDelivery = liveProduct['Shipping Fee (Rs.)'] || 'Free Across Pakistan';
                            const lImgRaw = liveProduct['Main Product Image  (Only 1)'];
                            let lImg = convertDriveLinkJS(lImgRaw, 'w1000');
                            if (lImg && !lImg.startsWith('http')) lImg = '../' + lImg;

                            // Update DOM with live data (if it changed)
                            if (lTitle) document.getElementById('liveTitle').innerText = lTitle;
                            if (lPrice) document.getElementById('livePrice').innerText = 'Rs. ' + lPrice;
                            if (lDesc) document.getElementById('liveDesc').innerText = lDesc;
                            if (lSizes) document.getElementById('liveSizes').innerText = lSizes;
                            if (lCat) document.getElementById('liveCategory').innerText = lCat;
                            if (lMat) document.getElementById('liveMaterial').innerText = lMat;
                            
                            if (lDelivery !== undefined) {{
                                let deliveryText = lDelivery;
                                if (!isNaN(lDelivery) && lDelivery.trim() !== '') {{
                                    deliveryText = 'Rs. ' + lDelivery;
                                }}
                                document.getElementById('liveDelivery').innerText = deliveryText;
                            }}
                            
                            if (lImg && lImg !== "") document.getElementById('liveMainImage').src = lImg;

                            // Save live data for the Add to Cart button
                            liveProductData = {{
                                title: lTitle || '{title}',
                                price: lPrice || '{price}',
                                image: lImg || '{image_url}',
                                shipping: lDelivery || '{delivery}'
                            }};
                        }}
                    }}
                }});
            }});
        </script>
        """
        
        final_html = custom_head + top_ui + page_html + footer + base_js
        
        filepath = os.path.join('products', f"{slug}.html")
        with open(filepath, 'w', encoding='utf-8') as pf:
            pf.write(final_html)
            
    print(f"Successfully generated {len(products)} product pages in 'products/' directory.")

if __name__ == "__main__":
    main()
