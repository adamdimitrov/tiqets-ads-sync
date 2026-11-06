/* ==========================================================================
   THE CRUISE DETECTIVE — INTERACTIVE CLIENT RUNTIME CONTROLLER
   Zero-dependency, semantic, responsive, WCAG-compliant (Desktop & Mobile)
   Features:
   1. Modern Navigation Header & Mobile Drawer
   2. Media Slider Carousel & Dynamic Counter
   3. Category Filter Tabs
   4. Floating Hybrid Sticky Bar (appears after scrolling past hero/deck)
   5. Interactive Bottom-Sheet / Modal Table of Contents
   ========================================================================== */

(function() {
  'use strict';

  // 1. Photo Slider Controller
  window.bpaSlide = function(btn, dir) {
    var media = btn.closest('.bpa-media');
    if (!media) return;
    var slider = media.querySelector('.bpa-slider');
    if (!slider) return;
    var w = slider.clientWidth;
    slider.scrollBy({ left: dir * w, behavior: 'smooth' });
  };

  window.bpaCount = function(slider) {
    var media = slider.closest('.bpa-media');
    if (!media) return;
    var pill = media.querySelector('.bpa-pill');
    if (!pill) return;
    var w = slider.clientWidth || 1;
    var idx = Math.min(Math.round(slider.scrollLeft / w) + 1, slider.children.length);
    pill.textContent = idx + ' / ' + slider.children.length;
  };

  // 2. Category Filter Tabs Controller
  window.lttFilterCards = function(cat, btn) {
    var buttons = document.querySelectorAll('.ltt-tab-btn');
    buttons.forEach(function(b) { b.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    
    var cards = document.querySelectorAll('#ltt-cards-deck .bpa-card');
    cards.forEach(function(card) {
      var cardCat = card.getAttribute('data-cat') || '';
      if (cat === 'all' || cardCat.indexOf(cat) !== -1) {
        card.style.display = 'block';
      } else {
        card.style.display = 'none';
      }
    });
  };

  // 3. Navigation Header & Mobile Drawer
  function initNav() {
    var toggle = document.getElementById('lttNavToggle');
    var drawer = document.getElementById('lttMobileDrawer');
    var dropdown = document.getElementById('lttExploreDropdown');
    var dropBtn = dropdown ? dropdown.querySelector('.ltt-dropdown-btn') : null;

    if (toggle && drawer) {
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        var isOpen = drawer.classList.contains('is-open');
        if (isOpen) {
          drawer.classList.remove('is-open');
          toggle.classList.remove('is-active');
          toggle.setAttribute('aria-expanded', 'false');
          drawer.setAttribute('aria-hidden', 'true');
        } else {
          drawer.classList.add('is-open');
          toggle.classList.add('is-active');
          toggle.setAttribute('aria-expanded', 'true');
          drawer.setAttribute('aria-hidden', 'false');
        }
      });

      drawer.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', function() {
          drawer.classList.remove('is-open');
          toggle.classList.remove('is-active');
          toggle.setAttribute('aria-expanded', 'false');
          drawer.setAttribute('aria-hidden', 'true');
        });
      });
    }

    if (dropBtn && dropdown) {
      dropBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        var open = dropdown.classList.toggle('is-open');
        dropBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    }

    document.addEventListener('click', function(e) {
      if (drawer && drawer.classList.contains('is-open') && !drawer.contains(e.target) && (!toggle || !toggle.contains(e.target))) {
        drawer.classList.remove('is-open');
        if (toggle) {
          toggle.classList.remove('is-active');
          toggle.setAttribute('aria-expanded', 'false');
        }
        drawer.setAttribute('aria-hidden', 'true');
      }
      if (dropdown && dropdown.classList.contains('is-open') && !dropdown.contains(e.target)) {
        dropdown.classList.remove('is-open');
        if (dropBtn) dropBtn.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        if (drawer && drawer.classList.contains('is-open')) {
          drawer.classList.remove('is-open');
          if (toggle) {
            toggle.classList.remove('is-active');
            toggle.setAttribute('aria-expanded', 'false');
          }
          drawer.setAttribute('aria-hidden', 'true');
        }
        if (dropdown && dropdown.classList.contains('is-open')) {
          dropdown.classList.remove('is-open');
          if (dropBtn) dropBtn.setAttribute('aria-expanded', 'false');
        }
        closeTocSheet();
      }
    });
  }

  // 4. Hybrid Sticky Bar & Bottom Sheet TOC
  function initStickyBarAndToc() {
    var stickyBar = document.getElementById('sticky-bar') || document.querySelector('.hybrid-sticky-bar');
    var tocBtn = document.getElementById('hybridTocBtn');
    var backdrop = document.getElementById('hybridBackdrop');
    var closeBtn = document.getElementById('hybridCloseBtn');
    var tocList = document.getElementById('hybridSheetList');

    if (!stickyBar) return;

    // Populate Mobile Bottom Sheet TOC from Cards or Details
    if (tocList && tocList.children.length === 0) {
      var cards = document.querySelectorAll('#ltt-cards-deck .bpa-card');
      cards.forEach(function(card) {
        var titleElem = card.querySelector('.bpa-title');
        var sublink = card.querySelector('.bpa-sublink');
        var priceElem = card.querySelector('.bpa-price');
        var targetId = sublink ? sublink.getAttribute('href') : '';
        if (titleElem && targetId) {
          var a = document.createElement('a');
          a.className = 'hybrid-toc-item';
          a.href = targetId;
          a.innerHTML = '<span>' + titleElem.textContent.trim() + '</span>' +
            (priceElem ? '<span class="hybrid-toc-price">' + priceElem.textContent.trim() + '</span>' : '');
          a.addEventListener('click', function() {
            closeTocSheet();
          });
          tocList.appendChild(a);
        }
      });
    }

    // Populate Desktop Sticky TOC (#toc)
    var desktopToc = document.getElementById('toc');
    if (desktopToc && desktopToc.children.length === 0) {
      var deckElem = document.getElementById('ltt-cards-deck') || document.querySelector('.comparison-table');
      if (deckElem) {
        var deckJump = document.createElement('a');
        deckJump.className = 'tocitem';
        deckJump.href = '#ltt-cards-deck';
        deckJump.textContent = '⚡ Comparison Deck';
        desktopToc.appendChild(deckJump);
      }

      var detailsCards = document.querySelectorAll('details.bpa-details-card');
      if (detailsCards.length > 0) {
        var bdHeader = document.getElementById('breakdown-header');
        if (bdHeader) {
          var bdJump = document.createElement('a');
          bdJump.className = 'tocitem';
          bdJump.href = '#breakdown-header';
          bdJump.textContent = '📋 Detailed Breakdown';
          desktopToc.appendChild(bdJump);
        }

        detailsCards.forEach(function(card) {
          var titleEl = card.querySelector('.bpa-details-title');
          var id = card.getAttribute('id');
          if (titleEl && id) {
            var item = document.createElement('a');
            item.className = 'tocitem';
            item.href = '#' + id;
            item.textContent = titleEl.textContent.trim();
            desktopToc.appendChild(item);
          }
        });
      }

      var buyingGuide = document.getElementById('buying-guide') || document.querySelector('.ltt-post-guide') || document.getElementById('faq-section');
      if (buyingGuide) {
        var bgJump = document.createElement('a');
        bgJump.className = 'tocitem';
        bgJump.href = '#' + (buyingGuide.id || 'buying-guide');
        bgJump.textContent = '💡 Field Advice & FAQs';
        desktopToc.appendChild(bgJump);
      }
    }

    // Scrollspy for Desktop TOC items
    if (desktopToc) {
      var tocItems = desktopToc.querySelectorAll('.tocitem');
      window.addEventListener('scroll', function() {
        var fromTop = window.scrollY + 140;
        var cur = null;
        tocItems.forEach(function(item) {
          var hash = item.getAttribute('href');
          if (hash && hash.startsWith('#')) {
            var target = document.querySelector(hash);
            if (target && target.offsetTop <= fromTop) {
              cur = item;
            }
          }
        });
        tocItems.forEach(function(item) {
          if (item === cur) {
            item.classList.add('active');
          } else {
            item.classList.remove('active');
          }
        });
      }, { passive: true });
    }

    // Show/hide sticky bar based on scroll position
    var thresholdElem = document.getElementById('ltt-cards-deck') || document.querySelector('.ltt-header-box');
    function onScroll() {
      var scrollY = window.pageYOffset || document.documentElement.scrollTop;
      var triggerPoint = thresholdElem ? (thresholdElem.offsetTop + 100) : 450;
      if (scrollY > triggerPoint) {
        stickyBar.classList.add('is-visible');
      } else {
        stickyBar.classList.remove('is-visible');
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // Open TOC sheet
    if (tocBtn && backdrop) {
      tocBtn.addEventListener('click', function(e) {
        e.preventDefault();
        backdrop.classList.add('is-open');
        document.body.style.overflow = 'hidden';
      });
    }

    // Close TOC sheet
    function closeTocSheet() {
      if (backdrop) {
        backdrop.classList.remove('is-open');
        document.body.style.overflow = '';
      }
    }

    if (closeBtn) closeBtn.addEventListener('click', closeTocSheet);
    if (backdrop) {
      backdrop.addEventListener('click', function(e) {
        if (e.target === backdrop) closeTocSheet();
      });
    }
  }

  // Global Expand / Collapse All Detailed Reviews controller
  window.toggleAllDetails = function(open) {
    var cards = document.querySelectorAll('details.bpa-details-card');
    cards.forEach(function(c) {
      if (open) {
        c.setAttribute('open', '');
      } else {
        c.removeAttribute('open');
      }
    });
  };

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initNav();
      initStickyBarAndToc();
    });
  } else {
    initNav();
    initStickyBarAndToc();
  }
})();
