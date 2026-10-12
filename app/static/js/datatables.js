(function ($) {
  'use strict';

  function collectFilters(selector) {
    var out = {};
    if (!selector) {
      return out;
    }
    $(selector)
      .find('[data-dt-filter]')
      .each(function () {
        if (this.value) {
          out[this.name] = this.value;
        }
      });
    return out;
  }

  function applyParams(target, columns, filterSelector) {
    if (target.order && target.order.length) {
      var col = columns[target.order[0].column];
      if (col && col.name) {
        target.sort = col.name;
        target.dir = target.order[0].dir;
      }
    }
    if (target.search && target.search.value) {
      target.q = target.search.value;
    }
    var filters = collectFilters(filterSelector);
    Object.keys(filters).forEach(function (key) {
      target[key] = filters[key];
    });
  }

  function updateBulk(dt) {
    var $table = $(dt.table().node());
    var total = $table.find('tbody input.dt-row-check').length;
    var checked = $table.find('tbody input.dt-row-check:checked').length;

    var bar = document.getElementById('dt-bulk-bar');
    if (bar) {
      bar.classList.toggle('hidden', checked === 0);
      var counter = bar.querySelector('[data-dt-selected]');
      if (counter) {
        counter.textContent = checked;
      }
    }

    var header = $table.find('thead .dt-check-all');
    if (header.length) {
      header.prop('checked', total > 0 && checked === total);
      header.prop('indeterminate', checked > 0 && checked < total);
    }
  }

  window.initServerTable = function (settings) {
    var $table = $(settings.table);

    var dt = $table.DataTable({
      serverSide: true,
      processing: true,
      autoWidth: false,
      pageLength: settings.pageLength || 25,
      lengthMenu: [25, 50, 100],
      searching: settings.searching !== false,
      ordering: settings.ordering !== false,
      order: settings.order || [],
      columns: settings.columns,
      language: {
        processing: 'Loading…',
        search: '',
        searchPlaceholder: settings.searchPlaceholder || 'Search…',
        lengthMenu: 'Show _MENU_',
        info: 'Showing _START_–_END_ of _TOTAL_',
        infoEmpty: 'No records',
        infoFiltered: '(filtered from _MAX_)',
        zeroRecords: 'No matching records',
        emptyTable: settings.emptyTable || 'No records found',
        loadingRecords: 'Loading…',
        paginate: { previous: 'Prev', next: 'Next' },
      },
      dom:
        "<'dt-toolbar flex flex-col gap-3 border-b border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between'<'dt-length'l><'dt-search'f>>" +
        't' +
        "<'dt-footer flex flex-col gap-3 border-t border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between'<'dt-info'i><'dt-pag'p>>",
      ajax: {
        url: settings.url,
        data: function (d) {
          applyParams(d, settings.columns, settings.filters);
        },
      },
      drawCallback: function () {
        updateBulk(dt);
        var info = dt.page.info();
        var records = document.querySelector('[data-dt-records]');
        if (records) {
          records.textContent = info.recordsDisplay.toLocaleString('id-ID');
        }
        if (settings.onDraw) {
          settings.onDraw(dt);
        }
      },
    });

    if (settings.initialSearch) {
      dt.search(settings.initialSearch).draw();
    }

    $table.on('change', 'input.dt-row-check, thead .dt-check-all', function () {
      if (this.classList.contains('dt-check-all')) {
        $table.find('tbody input.dt-row-check').prop('checked', this.checked);
      }
      updateBulk(dt);
    });

    $(document).on('click', '#dt-bulk-delete', function () {
      if (!$table.find('tbody input.dt-row-check:checked').length) {
        return;
      }
      window.dispatchEvent(
        new CustomEvent('confirm-modal', {
          detail: {
            heading: 'Delete selected records?',
            message: 'This permanently removes the selected records and cannot be undone.',
            confirmLabel: 'Delete',
            formId: 'bulk-form',
          },
        })
      );
    });

    $(document).on('click', '#dt-bulk-clear', function () {
      $table.find('tbody input.dt-row-check').prop('checked', false);
      $table.find('thead .dt-check-all').prop('checked', false);
      updateBulk(dt);
    });

    var form = settings.filters ? document.querySelector(settings.filters) : null;
    if (form) {
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        dt.ajax.reload();
      });
      var reset = document.getElementById('dt-filter-reset');
      if (reset) {
        reset.addEventListener('click', function (event) {
          event.preventDefault();
          form.reset();
          dt.search('').ajax.reload();
        });
      }
    }

    if (settings.exportUrl) {
      $(document).on('click', '.dt-export', function (event) {
        event.preventDefault();
        var format = this.getAttribute('data-format') || 'csv';
        var params = {};
        var order = dt.order();
        if (order.length) {
          var col = settings.columns[order[0][0]];
          if (col && col.name) {
            params.sort = col.name;
            params.dir = order[0][1];
          }
        }
        var search = dt.search();
        if (search) {
          params.q = search;
        }
        var filters = collectFilters(settings.filters);
        Object.keys(filters).forEach(function (key) {
          params[key] = filters[key];
        });
        params.format = format;
        window.location = settings.exportUrl + '?' + $.param(params);
      });
    }

    return dt;
  };

  $(document).on('click', '.dt-edit', function () {
    var url = this.getAttribute('data-edit-url');
    if (!url) {
      return;
    }
    if (window.htmx) {
      window.htmx.ajax('GET', url, { target: '#modal-content', swap: 'innerHTML' });
    }
    window.dispatchEvent(new CustomEvent('open-edit-modal'));
  });

  $(document).on('click', '.dt-delete', function () {
    var url = this.getAttribute('data-delete-url');
    if (!url) {
      return;
    }
    window.dispatchEvent(
      new CustomEvent('confirm-modal', {
        detail: {
          heading: 'Delete record?',
          message:
            'Delete ' +
            (this.getAttribute('data-delete-label') || 'this record') +
            ' permanently? This cannot be undone.',
          confirmLabel: 'Delete',
          action: url,
        },
      })
    );
  });
})(window.jQuery);
