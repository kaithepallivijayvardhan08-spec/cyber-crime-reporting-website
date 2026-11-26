(() => {
  const statuses = ['pending', 'under_review', 'investigating', 'resolved', 'rejected'];
  let page = 1, totalPages = 1;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[c]));

  async function loadComplaints() {
    const list = document.getElementById('staffComplaints');
    const message = document.getElementById('staffMessage');
    const filter = document.getElementById('statusFilter').value;
    message.textContent = 'Loading complaints…';
    list.replaceChildren();
    try {
      const url = API_BASE_URL + '/tracking/admin/complaints?page=' + page +
        '&limit=25&status=' + encodeURIComponent(filter);
      const response = await fetch(url, {
        headers: { Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '') }
      });
      const data = await response.json();
      if (!response.ok) {
        message.textContent = response.status === 401
          ? 'Sign in with an admin or investigator account.'
          : (data.error || 'Could not load complaints.');
        return;
      }
      totalPages = Math.max(1, data.pagination.total_pages);
      document.getElementById('pageInfo').textContent =
        'Page ' + data.pagination.page + ' of ' + totalPages + ' · ' + data.pagination.total + ' complaints';
      document.getElementById('previousPage').disabled = page <= 1;
      document.getElementById('nextPage').disabled = page >= totalPages;
      if (!data.complaints.length) {
        message.textContent = 'No complaints for this filter.';
        return;
      }
      message.textContent = '';
      list.innerHTML = data.complaints.map(item =>
        '<form class="staff-row" data-complaint-number="' + esc(item.complaint_number) + '">' +
          '<div><strong>' + esc(item.complaint_number) + '</strong><div>' + esc(item.crime_type) + '</div>' +
          '<div class="staff-muted">' + esc(item.reporter_name) + ' · ' + esc(item.reporter_email) + '</div></div>' +
          '<label>Current status<select name="status" required>' +
          statuses.map(status => '<option value="' + status + '"' + (item.status === status ? ' selected' : '') + '>' +
            esc(status.replace(/_/g, ' ')) + '</option>').join('') + '</select></label>' +
          '<label>Update note<textarea name="notes" maxlength="5000" placeholder="Short note for the timeline"></textarea></label>' +
          '<button class="btn btn-primary" type="submit">Save status</button></form>'
      ).join('');
    } catch (error) {
      console.error('Staff complaint list error:', error);
      message.textContent = 'Network error. Check that Flask is running.';
    }
  }

  async function updateStatus(form) {
    const message = document.getElementById('staffMessage');
    const formData = new FormData(form);
    message.textContent = 'Saving status…';
    try {
      const response = await fetch(API_BASE_URL + '/tracking/update-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '')
        },
        body: JSON.stringify({
          complaint_number: form.dataset.complaintNumber,
          status: formData.get('status'),
          notes: formData.get('notes')
        })
      });
      const data = await response.json();
      if (!response.ok) {
        message.textContent = data.error || 'Status update failed.';
        return;
      }
      message.textContent = data.complaint_number + ' updated to ' + data.status.replace(/_/g, ' ') + '.';
      await loadComplaints();
    } catch (error) {
      console.error('Status update error:', error);
      message.textContent = 'Network error. Check that Flask is running.';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('statusFilter').addEventListener('change', () => {
      page = 1;
      loadComplaints();
    });
    document.getElementById('refreshComplaints').addEventListener('click', loadComplaints);
    document.getElementById('previousPage').addEventListener('click', () => {
      if (page > 1) { page -= 1; loadComplaints(); }
    });
    document.getElementById('nextPage').addEventListener('click', () => {
      if (page < totalPages) { page += 1; loadComplaints(); }
    });
    document.getElementById('staffComplaints').addEventListener('submit', event => {
      if (event.target.matches('form[data-complaint-number]')) {
        event.preventDefault();
        updateStatus(event.target);
      }
    });
    loadComplaints();
  });
})();
