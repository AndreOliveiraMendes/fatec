document.querySelectorAll('.badge-head').forEach(el => {
    const url = el.dataset.url;
    const targetSelector = el.dataset.target;

    fetch(url)
        .then(r => r.json())
        .then(data => {
            // badge
            if (data.count > 0) {
                el.textContent = data.count;
                el.style.display = 'inline-block';
            }

            // alert (se existir na página)
            if (targetSelector) {
                const alertEl = document.querySelector(targetSelector);
                if (alertEl && data.list && data.list.length) {
                    const ul = alertEl.querySelector('.alert-list');
                    ul.innerHTML = '';

                    data.list.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        ul.appendChild(li);
                    });

                    alertEl.classList.remove('hide');
                }
            }
        });
});