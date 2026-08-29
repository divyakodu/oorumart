# Oorumart (`oorumart.in`) - Reusable Visual Component System (DSL Specification)

Derived from the visual breakdown of **Chumbak** (14 reference screenshots in `site_screenshots/Chumbak/`), this document formalizes the **Standard Component Primitives** for Oorumart storefronts.

Any vendor configuration (`yesfancy.yaml`, `sarveshpan.yaml`, `bagammaflowers.yaml`) can compose their homepage layout by chaining these named visual components in any order.

---

## 1. Catalog & Page Component Registry

```
+-----------------------------------------------------------------------+
| 1. announcement_bar (Ticker/Message Strip)                             |
+-----------------------------------------------------------------------+
| 2. primary_header (Logo, Category Tabs, Search Bar, Track, Cart)      |
+-----------------------------------------------------------------------+
| 3. poster_carousel (Hero Offer Banners)                               |
+-----------------------------------------------------------------------+
| 4. trust_features_banner (Icon + Feature Badges)                      |
+-----------------------------------------------------------------------+
| 5. product_carousel (Horizontal Product Slider)                       |
+-----------------------------------------------------------------------+
| 6. visual_category_block (Grid Tiles: 2-col, 3-col with Label Badges) |
+-----------------------------------------------------------------------+
| 7. brand_story_section (Ad-hoc Visual Narrative Tiles)                |
+-----------------------------------------------------------------------+
| 8. catalog_display_slice_and_dice (Sort, Filter, Grid Toggles)       |
+-----------------------------------------------------------------------+
| 9. product_card_overlay_add (Square Photo + Corner '+' Quick Add)     |
+-----------------------------------------------------------------------+
| 10. hooking_collection_slider (Cross-sell / "You May Also Like")      |
+-----------------------------------------------------------------------+
| 11. trailer_footer (Store Info, Hours, Socials, Links)               |
+-----------------------------------------------------------------------+
| 12. category_product_scroll_carousel (Category Chevron + Product Slider + See More) |
+-----------------------------------------------------------------------+
```

---

## 2. Component Definitions & Parameters

### Component 1: `announcement_bar`
* **Description**: Fixed or scrollable top banner featuring primary store messages.
* **Parameters**:
  * `messages`: Array of string announcements.
  * `auto_scroll_interval`: Time in seconds for auto-scroll.
  * `bg_color` & `text_color`: Theme colors.

### Component 2: `primary_header`
* **Description**: Sticky main header.
* **Features**:
  * Brand Logo (Text or Graphic).
  * Category Navigation Tabs (Hoverable/scrollable dropdowns).
  * Instant Search Bar with live text filter.
  * Track Order Icon (`/track/<order_id>`).
  * Cart Icon with live badge counter.

### Component 3: `poster_carousel`
* **Description**: Hero promotional banner slider.
* **Parameters**:
  * `items`: List of `{ image_url, title, subtitle, target_filter: { category, tag } }`.
  * `aspect_ratio`: Banner aspect ratio (e.g. `16:9` or `21:9`).

### Component 4: `trust_features_banner`
* **Description**: Ticker bar showcasing store USPs.
* **Examples**: *"Quick Local Delivery"*, *"Original Designs"*, *"Counter Pickup"*, *"30+ Local Stores"*.

### Component 5: `product_carousel`
* **Description**: Horizontal swipe product slider.
* **Parameters**:
  * `title`: Section heading (e.g., *"Rakhi & Gifts"*, *"Bestselling Novelties"*).
  * `filter_tag`: Filter products by tag (e.g. `tag: festive`).

### Component 6: `visual_category_block`
* **Description**: Grid of visual category image tiles linking to grouped product catalog views.
* **Parameters**:
  * `columns_per_row`: Number of tiles per row (e.g. `2`, `3`).
  * `items`: List of `{ name, image_url, target_category_id }`.
  * `badge_style`: Centered white pill badge over image.

### Component 7: `catalog_display_slice_and_dice`
* **Description**: Standardized full catalog display page.
* **Features**:
  * Category Title & Item count (`92 products`).
  * View Toggles: 2-column, 3-column, or List View.
  * Sort dropdown (`Price: Low to High`, `Popularity`, `Newest`).
  * Filter Drawer (Price Range, Tags, In-Stock Only).

### Component 8: `product_card_overlay_add` ⭐ (Signature Chumbak Card)
* **Description**: Clean square product image with a floating `+` button overlay in the bottom right corner.
* **Visual Structure**:
  - Image with optional `NEW ARRIVAL` dark badge on top-left.
  - White square `+` button in bottom-right corner of image container.
  - Title below image.
  - Price layout: `MRP : ₹ 455` (red accent) `₹ 649` (strikethrough) `30% OFF`.

### Component 9: `hooking_collection_slider`
* **Description**: Bottom recommendation carousel below product catalog ("Pairs Well With", "Buyers Also Bought").

### Component 10: `trailer_footer`
* **Description**: Rich store footer with brand links, opening hours, local pickup addresses, WhatsApp button, and copyright info.

### Component 12: `category_product_scroll_carousel` ⭐ (Category Chevron + Scrollable Catalog)
* **Description**: A hybrid row component featuring a fixed left-hand Category Banner Tile (with an angled right chevron divider) and a horizontally scrolling product catalog row on the right.
* **Visual Structure**:
  - **Left Tile**: Category image + bold Category title with a rightward chevron edge pointing to the products.
  - **Middle Track**: Up to `n` product cards showing image, title, price, and quick-add action.
  - **Terminal Card**: A dedicated "See More" / "Show More ➔" card linking directly to the full category catalog route (`/catalog?category=<id>`).

---

## 3. Sample Shop Configuration using Component Primitives

```yaml
shop:
  slug: "yesfancy"
  name: "Yes Fancy & Gift Corner"
  category: "gift_novelty"

  layout:
    - type: "announcement_bar"
      messages:
        - "Chumbak Express - Same day delivery in Bangalore"
        - "Festive Offer: Get 20% OFF on Gift Sets!"

    - type: "poster_carousel"
      items:
        - image: "/images/hero_banner.jpg"
          title: "Rare & Wild Collection"
          target_tag: "rare_wild"

    - type: "trust_features_banner"
      features:
        - { icon: "truck", label: "Quick Delivery" }
        - { icon: "shield", label: "Original Designs" }
        - { icon: "store", label: "Store Pickup" }

    - type: "product_carousel"
      title: "Rakhi and Gifts"
      filter_tag: "rakhi_gifts"

    - type: "visual_category_block"
      columns_per_row: 2
      items:
        - { name: "DINING", image: "/images/coasters.jpg", target_category: "dining" }
        - { name: "WATCHES", image: "/images/keychain.jpg", target_category: "watches" }

    - type: "catalog_display_slice_and_dice"
      title: "All Products"
      columns: 4
      enable_view_toggles: true
      enable_sort_and_filter: true
```
