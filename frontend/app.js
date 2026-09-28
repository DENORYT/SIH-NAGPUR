const API_BASE = 'http://127.0.0.1:8000/api';

function switchTab(tabId) {
    ['dashboard', 'graph', 'leaks', 'stylometry'].forEach(id => {
        document.getElementById(`view-${id}`).classList.add('hidden');
        document.getElementById(`tab-${id}`).classList.remove('bg-zinc-800/80', 'text-brand-500', 'border', 'border-zinc-700/50');
        document.getElementById(`tab-${id}`).classList.add('text-zinc-400');
    });
    
    document.getElementById(`view-${tabId}`).classList.remove('hidden');
    document.getElementById(`tab-${tabId}`).classList.remove('text-zinc-400');
    document.getElementById(`tab-${tabId}`).classList.add('bg-zinc-800/80', 'text-brand-500', 'border', 'border-zinc-700/50');

    if (tabId === 'graph') {
        if (!window.cy_initialized) {
            loadGraph();
        } else {
            window.cy.resize();
        }
    }
    
    if (tabId === 'leaks' && geoMap) {
        setTimeout(() => geoMap.invalidateSize(), 100);
    }
}

async function loadDashboard() {
    try {
        const statsRes = await fetch(`${API_BASE}/stats`);
        const stats = await statsRes.json();
        
        document.getElementById('stat-actors').innerText = stats.actor_count;
        document.getElementById('stat-leaks').innerText = stats.leak_count;
        document.getElementById('stat-crypto').innerText = (stats.link_counts.SAME_PGP || 0) + (stats.link_counts.SAME_WALLET || 0);
        document.getElementById('stat-style').innerText = stats.link_counts.STYLE_MATCH || 0;

        const actorsRes = await fetch(`${API_BASE}/actors`);
        const actors = await actorsRes.json();
        
        const tbody = document.getElementById('actor-table-body');
        tbody.innerHTML = '';
        
        actors.sort((a,b) => b.confidence_score - a.confidence_score).forEach((actor, idx) => {
            let riskBadge = actor.risk_category === 'DRUGS' ? '<span class="px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-[10px] font-semibold uppercase tracking-wider">DRUGS</span>' : 
                            actor.risk_category === 'ARMS' ? '<span class="px-2 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded text-[10px] font-semibold uppercase tracking-wider">ARMS</span>' : 
                            actor.risk_category === 'DATA' ? '<span class="px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-[10px] font-semibold uppercase tracking-wider">DATA</span>' : 
                            '<span class="px-2 py-1 bg-zinc-500/10 text-zinc-400 border border-zinc-500/20 rounded text-[10px] font-semibold uppercase tracking-wider">UNKNOWN</span>';
                            
            let barColor = actor.confidence_score > 80 ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]' : 
                           actor.confidence_score > 50 ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]' : 
                           'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]';

            tbody.innerHTML += `
                <tr class="hover:bg-zinc-800/50 transition-colors animate-fade-in" style="animation-delay: ${idx * 50}ms">
                    <td class="px-6 py-4 font-mono text-sm text-zinc-200">${actor.primary_handle}</td>
                    <td class="px-6 py-4">${riskBadge}</td>
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-3">
                            <span class="w-8 text-xs font-mono text-zinc-400">${actor.confidence_score.toFixed(0)}%</span>
                            <div class="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                                <div class="${barColor} h-full transition-all duration-1000" style="width: 0%" onload="this.style.width='${actor.confidence_score}%'" data-width="${actor.confidence_score}%"></div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 text-xs font-mono text-zinc-400">${actor.alias_count}</td>
                    <td class="px-6 py-4 text-right space-x-3">
                        <button onclick="viewActor('${actor.id}')" class="text-[11px] font-semibold text-brand-500 hover:text-brand-400 uppercase tracking-widest transition-colors shadow-sm hover:shadow-[0_0_10px_rgba(20,184,166,0.3)] bg-brand-500/10 px-3 py-1.5 rounded border border-brand-500/30">Inspect</button>
                    </td>
                </tr>
            `;
        });
        
        // Trigger width animation after DOM insertion
        setTimeout(() => {
            document.querySelectorAll('div[data-width]').forEach(el => {
                el.style.width = el.getAttribute('data-width');
            });
        }, 100);
    } catch (e) {
        console.error("API not reachable yet", e);
    }
}

let geoMap = null;

async function loadLeaks() {
    try {
        const res = await fetch(`${API_BASE}/leaks`);
        const leaks = await res.json();
        
        const tbody = document.getElementById('leaks-table-body');
        tbody.innerHTML = '';
        
        if (!geoMap) {
            geoMap = L.map('map').setView([40, 10], 2);
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
            }).addTo(geoMap);
        } else {
            geoMap.eachLayer((layer) => {
                if (layer instanceof L.Marker) {
                    geoMap.removeLayer(layer);
                }
            });
        }
        
        leaks.forEach(leak => {
            if (leak.evidence && leak.evidence.lat && leak.evidence.lng) {
                L.marker([leak.evidence.lat, leak.evidence.lng], { icon: L.divIcon({ className: 'custom-pulse-marker', html: '<div class="w-3 h-3 bg-rose-500 rounded-full animate-pulse shadow-[0_0_15px_rgba(244,63,94,1)]"></div>', iconSize: [12, 12], iconAnchor: [6, 6] }) })
                 .addTo(geoMap)
                 .bindPopup(`<b>${leak.matched_clearnet_domain}</b><br>IP: ${leak.matched_clearnet_ip}<br>Type: ${leak.type}`);
            }

            let clearnetTarget = leak.matched_clearnet_ip || leak.matched_clearnet_domain;
            let shodanBtn = leak.matched_clearnet_ip 
                ? `<button onclick="runShodanScan('${leak.matched_clearnet_ip}')" class="ml-4 bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 border border-brand-500/30 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-widest transition-colors">OSINT Scan</button>`
                : '';

            tbody.innerHTML += `
                <tr class="hover:bg-zinc-800/50 transition-colors">
                    <td class="px-6 py-4">
                        <span class="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-1 rounded text-[10px] font-bold tracking-wider">${leak.type}</span>
                    </td>
                    <td class="px-6 py-4 font-mono text-xs text-zinc-400">${leak.onion_address || 'N/A'}</td>
                    <td class="px-6 py-4 flex items-center">
                        <span class="font-mono text-xs text-brand-400 font-medium">${clearnetTarget || 'N/A'}</span>
                        ${shodanBtn}
                    </td>
                    <td class="px-6 py-4">
                        <div class="text-xs font-mono text-zinc-400">${leak.confidence.toFixed(1)}%</div>
                    </td>
                </tr>
            `;
        });
        
        setTimeout(() => geoMap.invalidateSize(), 100);

    } catch(e) {}
}

async function runShodanScan(ip) {
    const modal = document.getElementById('shodan-modal');
    const content = document.getElementById('shodan-content');
    
    modal.classList.remove('hidden');
    content.innerHTML = `
        <div class="flex justify-center items-center py-12 flex-col">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500 mb-4"></div>
            <div class="text-xs text-brand-500 font-mono tracking-widest uppercase animate-pulse">Querying Live Shodan API for ${ip}...</div>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/osint/shodan/${ip}`);
        const data = await res.json();

        if (data.error) {
            content.innerHTML = `
                <div class="bg-surface p-6 rounded border border-border text-center">
                    <p class="text-zinc-400 font-mono text-sm">${data.message}</p>
                </div>
            `;
            return;
        }

        let portsHtml = data.ports.length > 0 
            ? data.ports.map(p => `<span class="px-2 py-1 bg-brand-500/10 border border-brand-500/30 text-brand-400 rounded text-[11px] font-mono">${p}</span>`).join(' ') 
            : '<span class="text-zinc-500 text-xs italic">No open ports</span>';
            
        let vulnsHtml = data.vulns.length > 0 
            ? data.vulns.map(v => `<span class="px-2 py-1 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded text-[11px] font-mono">${v}</span>`).join(' ') 
            : '<span class="text-emerald-500 text-xs italic font-semibold uppercase tracking-wider">No known vulnerabilities</span>';

        content.innerHTML = `
            <div class="grid grid-cols-2 gap-6">
                <div class="bg-panel border border-border p-4 rounded-lg">
                    <h3 class="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Target IP</h3>
                    <p class="text-lg font-mono text-zinc-100">${data.ip}</p>
                </div>
                <div class="bg-panel border border-border p-4 rounded-lg">
                    <h3 class="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Organization / ISP</h3>
                    <p class="text-sm font-semibold text-zinc-200">${data.org}</p>
                    <p class="text-xs text-zinc-400 mt-1">${data.isp}</p>
                </div>
            </div>
            
            <div class="mt-6">
                <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Open Ports & Services</h3>
                <div class="bg-surface p-4 border border-border rounded-lg flex flex-wrap gap-2">
                    ${portsHtml}
                </div>
            </div>
            
            <div class="mt-6">
                <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Vulnerability Exposure</h3>
                <div class="bg-surface p-4 border border-border rounded-lg flex flex-wrap gap-2">
                    ${vulnsHtml}
                </div>
            </div>
        `;
    } catch(e) {
        content.innerHTML = `<p class="text-rose-500 text-sm">Failed to connect to Shodan API.</p>`;
    }
}

async function loadStylometry() {
    try {
        const res = await fetch(`${API_BASE}/trust-links?type=STYLE_MATCH`);
        const links = await res.json();
        
        const container = document.getElementById('stylometry-container');
        container.innerHTML = '';
        
        if(links.length === 0) {
            container.innerHTML = '<p class="text-zinc-500 text-sm">No style matches found.</p>';
            return;
        }
        
        links.forEach(link => {
            let statusBadge = link.ai_suggested 
                ? '<span class="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] uppercase font-semibold tracking-wider">Unverified</span>' 
                : '<span class="bg-brand-500/10 text-brand-500 border border-brand-500/20 px-2 py-0.5 rounded text-[10px] uppercase font-semibold tracking-wider">Verified</span>';
                
            let verifyBtn = link.ai_suggested 
                ? `<button onclick="verifyLink('${link.id}')" class="bg-brand-500/10 hover:bg-brand-500/20 text-brand-500 border border-brand-500/50 px-3 py-1.5 rounded text-xs font-semibold tracking-widest uppercase transition-all">Verify Match</button>` 
                : `<button class="bg-zinc-800 text-zinc-500 border border-zinc-700 px-3 py-1.5 rounded text-xs font-semibold tracking-widest uppercase cursor-not-allowed" disabled>Verified</button>`;

            let xaiHtml = '';
            if (link.evidence && link.evidence.shared_n_grams && link.evidence.shared_n_grams.length > 0) {
                let ngrams = link.evidence.shared_n_grams.map(n => `<span class="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-sm text-[11px] mr-2 font-mono">"${n}"</span>`).join('');
                xaiHtml = `<div class="mt-4 pt-4 border-t border-border">
                    <p class="text-[10px] text-zinc-500 mb-2 uppercase tracking-widest font-semibold">Explainable AI (Shared Syntax)</p>
                    <div class="flex flex-wrap">${ngrams}</div>
                </div>`;
            }

            container.innerHTML += `
                <div class="bg-panel p-6 rounded-lg border border-border shadow-sm flex flex-col justify-between">
                    <div class="flex justify-between items-start w-full">
                        <div>
                            <div class="flex items-center gap-3 mb-2">
                                <span class="text-zinc-200 font-mono text-sm bg-surface px-2 py-1 rounded border border-border">${link.actor_a_id.substring(0,8)}</span> 
                                <span class="text-zinc-500 tracking-widest text-[10px] uppercase font-bold">Matched With</span> 
                                <span class="text-zinc-200 font-mono text-sm bg-surface px-2 py-1 rounded border border-border">${link.actor_b_id.substring(0,8)}</span>
                                ${statusBadge}
                            </div>
                            <div class="text-xs text-zinc-500 mt-2">Cosine Similarity: <span class="text-zinc-300 font-mono ml-1">${(link.strength_score / 100).toFixed(4)}</span></div>
                        </div>
                        <div>
                            ${verifyBtn}
                        </div>
                    </div>
                    ${xaiHtml}
                </div>
            `;
        });
    } catch(e) {}
}

async function verifyLink(linkId) {
    await fetch(`${API_BASE}/trust-links/${linkId}/verify`, { method: 'POST' });
    loadStylometry();
    loadDashboard();
}

async function viewActor(actorId) {
    try {
        const res = await fetch(`${API_BASE}/actors/${actorId}`);
        const actor = await res.json();
        
        scrambleText(document.getElementById('modal-title'), `Dossier: ${actor.primary_handle}`);
        document.getElementById('ai-briefing-content').innerHTML = '<span class="animate-pulse text-zinc-500">Generating intelligence summary...</span>';
        
        let leaksHtml = actor.related_leaks.map(l => `
            <li class="bg-surface p-3 rounded-md border border-border mb-2">
                <div class="flex justify-between items-center mb-1">
                    <div class="text-rose-400 font-semibold text-[10px] uppercase tracking-widest">${l.type}</div>
                    <div class="text-zinc-500 text-[10px] font-mono">Conf: ${l.confidence}%</div>
                </div>
                <div class="font-mono text-xs break-all text-zinc-400">Target: ${l.onion_address}</div>
                <div class="font-mono text-xs break-all text-brand-400">Clearnet: ${l.matched_clearnet_ip || l.matched_clearnet_domain}</div>
            </li>
        `).join('');
        if (!leaksHtml) leaksHtml = '<p class="text-xs text-zinc-500 italic">No infrastructure leaks detected.</p>';

        const content = `
            <div class="grid grid-cols-2 gap-8">
                <div>
                    <div class="mb-6">
                        <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Threat Profile</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-surface p-3 rounded-md border border-border">
                                <div class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Risk Category</div>
                                <div class="font-medium text-sm text-zinc-200">${actor.risk_category}</div>
                            </div>
                            <div class="bg-surface p-3 rounded-md border border-border">
                                <div class="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Confidence</div>
                                <div class="font-mono font-medium text-sm text-brand-400">${actor.confidence_score}%</div>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Aliases & Personas</h3>
                        <ul class="space-y-2">
                            ${actor.aliases.map(a => `
                                <li class="bg-surface px-3 py-2 rounded-md border border-border flex justify-between items-center">
                                    <span class="font-mono text-sm text-zinc-300">${a.handle}</span>
                                    <span class="text-[10px] text-zinc-500 uppercase tracking-widest">${a.platform}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
                <div>
                    <div class="mb-6">
                        <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Network & Crypto Identifiers</h3>
                        <ul class="space-y-2 max-h-40 overflow-y-auto pr-2">
                            ${actor.identifiers.map(i => {
                                let scanBtn = i.type === 'WALLET_ETH' ? `<button onclick="runCryptoScan('${i.value}')" class="mt-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded text-[10px] uppercase font-bold tracking-widest transition-colors w-full">Trace on Etherscan</button>` : '';
                                return `
                                <li class="bg-surface p-2 rounded-md border border-border">
                                    <span class="text-[10px] text-zinc-500 block mb-1 uppercase tracking-wider font-semibold">${i.type}</span>
                                    <span class="font-mono text-xs break-all text-zinc-300">${i.value}</span>
                                    ${scanBtn}
                                </li>
                                `;
                            }).join('')}
                        </ul>
                    </div>
                    
                    <div>
                        <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3 flex items-center justify-between">
                            Infrastructure Leaks
                            <span class="bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded text-[10px] border border-rose-500/20">${actor.related_leaks.length}</span>
                        </h3>
                        <ul class="space-y-2 max-h-40 overflow-y-auto pr-2">
                            ${leaksHtml}
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="mt-8 pt-4 border-t border-border flex justify-end">
                <a href="${API_BASE}/reports/${actor.id}/export" target="_blank" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 px-6 py-2 rounded-md transition-colors text-xs font-semibold tracking-wider uppercase">Export PDF Report</a>
            </div>
        `;
        
        document.getElementById('modal-content').innerHTML = content;
        document.getElementById('actor-modal').classList.remove('hidden');

        // Fetch AI Briefing
        fetch(`${API_BASE}/actors/${actorId}/briefing`)
            .then(r => r.json())
            .then(data => {
                let briefingText = data.briefing || "Failed to generate briefing.";
                let bContainer = document.getElementById('ai-briefing-content');
                bContainer.innerHTML = '';
                // Typewriter effect
                let i = 0;
                let typing = setInterval(() => {
                    if (i < briefingText.length) {
                        bContainer.innerHTML += briefingText.charAt(i);
                        i++;
                    } else {
                        clearInterval(typing);
                    }
                }, 15);
            })
            .catch(e => {
                document.getElementById('ai-briefing-content').innerHTML = '<span class="text-rose-500">Error connecting to AI service.</span>';
            });
            
    } catch(e) {
        console.error(e);
    }
}

function closeModal() {
    document.getElementById('actor-modal').classList.add('hidden');
}

async function loadGraph() {
    try {
        const res = await fetch(`${API_BASE}/graph`);
        const data = await res.json();
        
        const elements = [];
        
        data.nodes.forEach(n => {
            let color = n.risk === 'DRUGS' ? '#10b981' : 
                        n.risk === 'ARMS' ? '#f43f5e' : 
                        n.risk === 'DATA' ? '#3b82f6' : '#71717a';
            elements.push({
                data: { 
                    id: n.id, 
                    label: n.label,
                    risk: n.risk,
                    color: color
                }
            });
        });
        
        data.edges.forEach(l => {
            elements.push({
                data: {
                    id: l.source + '-' + l.target,
                    source: l.source,
                    target: l.target,
                    label: l.type,
                    weight: l.strength
                }
            });
        });

        window.cy = cytoscape({
            container: document.getElementById('cy'),
            elements: elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': 'data(color)',
                        'label': 'data(label)',
                        'color': '#f4f4f5',
                        'font-family': 'Inter, sans-serif',
                        'font-size': '11px',
                        'font-weight': '600',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'text-margin-y': 6,
                        'text-outline-color': '#09090b',
                        'text-outline-width': 2,
                        'width': '18px',
                        'height': '18px',
                        'border-width': 2,
                        'border-color': '#18181b'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1.5,
                        'line-color': '#3f3f46',
                        'target-arrow-color': '#3f3f46',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '8px',
                        'font-family': 'Inter, sans-serif',
                        'font-weight': '500',
                        'color': '#a1a1aa',
                        'text-rotation': 'autorotate',
                        'text-background-color': '#09090b',
                        'text-background-opacity': 1,
                        'text-background-shape': 'roundrectangle',
                        'text-background-padding': 2,
                        'arrow-scale': 0.8
                    }
                },
                {
                    selector: 'edge[label="STYLE_MATCH"]',
                    style: {
                        'line-style': 'dashed',
                        'line-color': '#818cf8',
                        'target-arrow-color': '#818cf8',
                        'width': 1.5
                    }
                },
                {
                    selector: 'edge[label="SAME_PGP"]',
                    style: {
                        'line-color': '#10b981',
                        'target-arrow-color': '#10b981'
                    }
                },
                {
                    selector: 'edge[label="SAME_WALLET"]',
                    style: {
                        'line-color': '#f59e0b',
                        'target-arrow-color': '#f59e0b'
                    }
                },
                {
                    selector: 'edge[label="VOUCHED_FOR"]',
                    style: {
                        'line-color': '#3b82f6',
                        'target-arrow-color': '#3b82f6'
                    }
                }
            ],
            layout: {
                name: 'cose',
                idealEdgeLength: 100,
                nodeOverlap: 20,
                refresh: 20,
                fit: true,
                padding: 40,
                randomize: true,
                componentSpacing: 100,
                nodeRepulsion: 400000,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            }
        });
        
        window.cy.on('tap', 'node', function(evt){
            var node = evt.target;
            viewActor(node.id());
        });
        
        window.cy_initialized = true;
    } catch(e) {}
}

document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
        closeModal();
    }
});

loadDashboard();
loadLeaks();
loadStylometry();

async function runCryptoScan(address) {
    const modal = document.getElementById('crypto-modal');
    const content = document.getElementById('crypto-content');
    
    modal.classList.remove('hidden');
    content.innerHTML = `
        <div class="flex justify-center items-center py-12 flex-col">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mb-4"></div>
            <div class="text-xs text-emerald-500 font-mono tracking-widest uppercase animate-pulse">Querying Live Ethereum Blockchain...</div>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/osint/crypto/${address}`);
        const data = await res.json();

        if (data.error) {
            content.innerHTML = `
                <div class="bg-surface p-6 rounded border border-border text-center">
                    <p class="text-zinc-400 font-mono text-sm">${data.message}</p>
                </div>
            `;
            return;
        }

        let txsHtml = data.transactions.length > 0 
            ? data.transactions.map(tx => `
                <div class="bg-surface p-3 border border-border rounded mb-2">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-[10px] text-zinc-500 font-mono uppercase tracking-widest">TX HASH</span>
                        <span class="text-[10px] font-bold text-emerald-400">${tx.value.toFixed(4)} ETH</span>
                    </div>
                    <div class="text-xs text-zinc-300 font-mono truncate">${tx.hash}</div>
                </div>
            `).join('') 
            : '<span class="text-zinc-500 text-xs italic">No recent transactions. This is typical for washed/tumbled threat actor wallets.</span>';

        content.innerHTML = `
            <div class="bg-panel border border-border p-5 rounded-lg mb-6 text-center">
                <h3 class="text-[10px] text-zinc-500 uppercase tracking-widest mb-2">Current Wallet Balance</h3>
                <div class="text-4xl font-mono font-bold text-emerald-400">${data.balance_eth.toFixed(4)} <span class="text-xl text-emerald-500/50">ETH</span></div>
                <div class="text-xs text-zinc-500 font-mono mt-2">${data.address}</div>
            </div>
            
            <div class="mt-6">
                <h3 class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-3 flex items-center justify-between">
                    Recent Blockchain Transactions
                    <span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-[9px] uppercase tracking-widest">Live</span>
                </h3>
                <div class="max-h-64 overflow-y-auto pr-2">
                    ${txsHtml}
                </div>
            </div>
        `;
    } catch(e) {
        content.innerHTML = `<p class="text-rose-500 text-sm">Failed to connect to Etherscan API.</p>`;
    }
}

// Boot Sequence Logic
const bootScreen = document.getElementById("boot-screen");
const bootText = document.getElementById("boot-text");
const bootMessages = [
    "INITIALIZING SHADOWLINK OS v4.2.1...",
    "CONNECTING TO ONION ROUTING NETWORK...",
    "ESTABLISHING SECURE TUNNEL...",
    "LOADING DE-ANONYMIZATION MODULES...",
    "[OK] INFRA_MATCHER MODULE LOADED",
    "[OK] IDENTITY_GRAPH MODULE LOADED",
    "[OK] STYLOMETRY MODULE LOADED",
    "SYNCING THREAT INTELLIGENCE DATABASES...",
    "DECRYPTING INTERCEPTED PGP KEYS...",
    "READY."
];

let msgIndex = 0;
function showNextBootMessage() {
    if (msgIndex < bootMessages.length) {
        const p = document.createElement("p");
        p.className = "mb-1";
        p.innerText = bootMessages[msgIndex];
        bootText.appendChild(p);
        bootText.scrollTop = bootText.scrollHeight;
        msgIndex++;
        setTimeout(showNextBootMessage, Math.random() * 300 + 100);
    } else {
        setTimeout(() => {
            bootScreen.classList.add("opacity-0", "pointer-events-none");
            setTimeout(() => bootScreen.remove(), 700);
        }, 500);
    }
}
// Start Boot Sequence
window.addEventListener("DOMContentLoaded", () => {
    setTimeout(showNextBootMessage, 500);
});


// Live Intercepts Logic
async function initLiveIntercepts() {
    const feed = document.getElementById("intercept-feed");
    if (!feed) return;
    
    try {
        const res = await fetch(`${API_BASE}/intercepts`);
        const posts = await res.json();
        let idx = 0;
        
        function appendIntercept() {
            if (idx >= posts.length) idx = 0;
            const post = posts[idx];
            idx++;
            
            const div = document.createElement("div");
            div.className = "text-brand-500/80 animate-fade-in border-l-2 border-brand-500/50 pl-3";
            div.innerHTML = `
                <div class="flex justify-between text-[10px] opacity-70 mb-1">
                    <span>[${post.timestamp.split("T")[0]}] @${post.handle}</span>
                    <span>SOURCE: ${post.platform}</span>
                </div>
                <div class="text-zinc-300">"${post.text}"</div>
            `;
            
            feed.appendChild(div);
            if (feed.children.length > 4) {
                feed.removeChild(feed.firstChild);
            }
            
            setTimeout(appendIntercept, Math.random() * 4000 + 2000);
        }
        appendIntercept();
    } catch (e) {
        console.error("Failed to load intercepts", e);
    }
}

// Attach to loadDashboard
const oldLoadDashboard = loadDashboard;
loadDashboard = async function() {
    await oldLoadDashboard();
    initLiveIntercepts();
};


// Hacker Scramble Effect
function scrambleText(element, finalString, duration = 800) {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*";
    let iteration = 0;
    const maxIterations = finalString.length;
    const interval = setInterval(() => {
        element.innerText = finalString.split("").map((letter, index) => {
            if(index < iteration) return letter;
            return chars[Math.floor(Math.random() * chars.length)];
        }).join("");
        
        if(iteration >= maxIterations){
            clearInterval(interval);
        }
        iteration += 1 / (duration / 50 / maxIterations);
    }, 50);
}



