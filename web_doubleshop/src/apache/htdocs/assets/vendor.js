(function(){
    const _p = [
        {id:"A1",n:"Classic Cola",p:3,s:4,i:"assets/img/cola.png"},
        {id:"B1",n:"Chips",p:2,s:6,i:"assets/img/chips.png"},
        {id:"C1",n:"Spring Water",p:1,s:10,i:"assets/img/water.png"}
    ];


    let _bal = parseInt(sessionStorage.getItem('v_bal')) || 0;
    let _hist = JSON.parse(sessionStorage.getItem('v_hist')) || [];
    

    let _inv = JSON.parse(sessionStorage.getItem('v_inv'));

    if(!_inv || _inv.length !== _p.length) _inv = JSON.parse(JSON.stringify(_p));

    let _sid = localStorage.getItem('v_sid');
    if(!_sid) { 
        _sid = Math.random().toString(36).substring(2) + Date.now().toString(36); 
        localStorage.setItem('v_sid', _sid); 
    }

    // --- UTILS ---
    const $ = s => document.querySelector(s);
    const nt = n => `$ ${n}`;
    
    const _save = () => {
        sessionStorage.setItem('v_bal', _bal);
        sessionStorage.setItem('v_hist', JSON.stringify(_hist));
        sessionStorage.setItem('v_inv', JSON.stringify(_inv));
    };

    const _toast = m => {
        const t = $('#toast');
        if(t) {
            t.textContent = m; 
            t.classList.add('show'); 
            setTimeout(() => t.classList.remove('show'), 2000);
        } else {
            console.log("Toast:", m);
        }
    };

    // --- RENDERING UI ---
    const _renderLog = () => {
        const list = $('#purchasedList');
        if(!list) return;
        list.innerHTML = '';
        
        if(_hist.length === 0) {
            list.innerHTML = '<li style="padding:10px; text-align:center; color:#ccc; font-style:italic">No transactions yet</li>';
        } else {
            _hist.slice().reverse().slice(0, 10).forEach(item => {
                const li = document.createElement('li'); li.className = 'log-item';
                li.innerHTML = `<span>${item.n}</span> <span>-${nt(item.p)}</span>`;
                list.appendChild(li);
            });
        }
    };

    const _updateUI = () => {
        if($('#balance')) $('#balance').textContent = nt(_bal);
        _renderLog();
    };

    const _renderGrid = (filter="") => {
        const grid = $('#grid');
        if(!grid) return;
        grid.innerHTML = '';
        
        _inv.filter(p => !filter || p.n.toLowerCase().includes(filter.toLowerCase())).forEach(p => {
            const card = document.createElement('article'); card.className = 'item-card';
            card.innerHTML = `
                <div class="thumb"><img src="${p.i}"></div>
                <div class="item-name">${p.n}</div>
                <div class="item-meta"><span class="item-price">${nt(p.p)}</span> | Stock: ${p.s}</div>
                <button class="btn-buy" data-id="${p.id}" ${p.s===0?'disabled':''}>${p.s===0?'Out of Stock':'Purchase'}</button>`;
            grid.appendChild(card);
        });
    };

    window.actionBuy = (id) => {
        const p = _inv.find(x => x.id === id);
        if(!p) return;
        if(_bal < p.p) return _toast('Insufficient funds');
        if(p.s <= 0) return _toast('Out of Stock');

        _bal -= p.p; 
        p.s--;
        _hist.push({n: p.n, p: p.p});
        
        _save(); 
        _updateUI(); 
        _renderGrid($('#search').value);
        _toast(`Purchased: ${p.n}`);
    };

    const init = () => {
        console.log("Vendor System Initialized"); 
        _updateUI(); 
        _renderGrid();

        const grid = $('#grid');
        if(grid) {
            grid.addEventListener('click', e => {
                if(e.target.classList.contains('btn-buy')) {
                    window.actionBuy(e.target.dataset.id);
                }
            });
        }

        document.querySelectorAll('.coin-btn').forEach(b => {
            b.addEventListener('click', e => {
                const amt = parseInt(e.target.dataset.amt);
                _bal += amt;
                _save(); 
                _updateUI();
                console.log("Added coin:", amt);
            });
        });

        const search = $('#search');
        if(search) search.addEventListener('input', e => _renderGrid(e.target.value));

        const btnRefund = $('#returnChange');
        if(btnRefund) {
            btnRefund.addEventListener('click', () => {
                if(_hist.length === 0) return _toast('Nothing to refund');
                
                let total = 0; 
                _hist.forEach(h => total += h.p);
                
                _bal += total; 
                _hist = [];
                
                _save(); 
                _updateUI(); 
                _toast(`Refunded ${nt(total)}`);
            });
        }

        const btnClear = $('#clear');
        if(btnClear) {
            btnClear.addEventListener('click', () => {
                _bal = 0; 
                _save(); 
                _updateUI(); 
                _toast('Balance cleared');
            });
        }

        const btnRestock = $('#restock');
        if(btnRestock) {
            btnRestock.addEventListener('click', () => {
                _bal = 0;
                _hist = [];
                _inv = JSON.parse(JSON.stringify(_p));
                
                _save();
                _updateUI();
                _renderGrid();
                _toast('System Reset & Restocked');
            });
        }

        const _base = "\x2f\x61\x70\x69\x2f\x72\x65\x63\x65\x69\x70\x74\x2e\x6a\x73\x70\x3f\x69\x64\x3d";
        const btnReceipt = $('#viewReceipt');
        
        if(btnReceipt) {
            btnReceipt.addEventListener('click', async () => {
                _toast('Generating receipt...');
                try {
                    // Prepara i dati per il backend
                    const formData = new URLSearchParams();
                    formData.append('sid', _sid);
                    formData.append('items', JSON.stringify(_hist));

                    const res = await fetch('/api/checkout.jsp', { 
                        method: 'POST', 
                        body: formData 
                    });
                    
                    if(res.ok) {
                        const fileTarget = (_hist.length === 0) ? "sample.txt" : `${_sid}.log`;
                        window.open(_base + fileTarget, '_blank');
                    } else {
                        _toast('Server Error');
                    }
                } catch(e) {
                    console.error(e);
                    _toast('Connection Error');
                }
            });
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();