/**
 * Trace Viewer - Reusable JavaScript module for displaying traces
 */

const TraceViewer = (function() {
    'use strict';
    
    // Trace type configurations
    const TRACE_TYPE_CONFIG = {
        chat_interaction: {
            label: 'Chat',
            color: '#3b82f6',
            icon: '💬'
        },
        recommendation_generated: {
            label: 'Recommendation',
            color: '#10b981',
            icon: '📋'
        },
        recommendation_overridden: {
            label: 'Override',
            color: '#f59e0b',
            icon: '⚠️'
        },
        user_flagged: {
            label: 'Flag',
            color: '#ef4444',
            icon: '🚩'
        },
        persona_assigned: {
            label: 'Persona',
            color: '#a855f7',
            icon: '👤'
        },
        features_computed: {
            label: 'Features',
            color: '#64748b',
            icon: '⚙️'
        }
    };
    
    /**
     * Format a trace for display
     */
    function formatTrace(trace) {
        const config = TRACE_TYPE_CONFIG[trace.trace_type] || {
            label: trace.trace_type,
            color: '#64748b',
            icon: '•'
        };
        
        return {
            ...trace,
            type_label: config.label,
            type_color: config.color,
            type_icon: config.icon,
            timestamp_formatted: formatTimestamp(trace.timestamp)
        };
    }
    
    /**
     * Format timestamp for display
     */
    function formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
    
    /**
     * Render trace modal
     */
    function renderTraceModal(trace) {
        const modal = document.getElementById('traceModal');
        if (!modal) {
            console.error('Trace modal not found');
            return;
        }
        
        const formatted = formatTrace(trace);
        const traceJson = JSON.stringify(trace, null, 2);
        
        // Update modal title
        const title = modal.querySelector('.modal-title');
        if (title) {
            title.textContent = `${formatted.type_icon} ${formatted.type_label} - ${formatted.trace_id}`;
        }
        
        // Update trace content
        const content = modal.querySelector('#traceContent');
        if (content) {
            content.textContent = traceJson;
        }
        
        // Store current trace for copy functionality
        window.currentTraceData = trace;
        
        // Show modal
        modal.classList.remove('hidden');
        modal.classList.add('show');
    }
    
    /**
     * Close trace modal
     */
    function closeTraceModal() {
        const modal = document.getElementById('traceModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('show');
        }
        window.currentTraceData = null;
    }
    
    /**
     * Copy trace to clipboard
     */
    async function copyTraceToClipboard() {
        if (!window.currentTraceData) return;
        
        const traceJson = JSON.stringify(window.currentTraceData, null, 2);
        
        try {
            await navigator.clipboard.writeText(traceJson);
            
            // Show feedback
            const btn = document.querySelector('.modal-content .btn');
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#10b981';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                }, 2000);
            }
        } catch (err) {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
        }
    }
    
    /**
     * Render timeline event
     */
    function renderTimelineEvent(event) {
        const formatted = formatTrace(event);
        
        return `
            <div class="timeline-event" data-trace-id="${escapeHtml(event.trace_id)}">
                <div class="timeline-marker" style="background: ${formatted.type_color}">
                    <span class="timeline-icon">${formatted.type_icon}</span>
                </div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="timeline-type-badge" style="
                            background: ${formatted.type_color}15;
                            color: ${formatted.type_color};
                            border-color: ${formatted.type_color}
                        ">${formatted.type_label}</span>
                        <span class="timeline-timestamp">${formatted.timestamp_formatted}</span>
                    </div>
                    <div class="timeline-summary">${escapeHtml(event.summary)}</div>
                    ${event.persona ? `<div class="timeline-persona">Persona: ${escapeHtml(event.persona)}</div>` : ''}
                    <button onclick="TraceViewer.showTrace('${escapeHtml(event.trace_id)}')" class="timeline-details-btn">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Render trace type badge
     */
    function renderTypeBadge(traceType) {
        const config = TRACE_TYPE_CONFIG[traceType] || {
            label: traceType,
            color: '#64748b',
            icon: '•'
        };
        
        return `
            <span class="trace-type-badge" style="
                background: ${config.color}15;
                color: ${config.color};
                border: 1px solid ${config.color}
            ">
                ${config.icon} ${config.label}
            </span>
        `;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Show trace by ID
     */
    async function showTrace(traceId) {
        try {
            const response = await fetch(`${window.API_BASE_URL || 'http://localhost:8000'}/api/traces/${traceId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch trace');
            }
            const data = await response.json();
            renderTraceModal(data.data);
        } catch (error) {
            console.error('Error loading trace:', error);
            alert('Failed to load trace details');
        }
    }
    
    // Public API
    return {
        formatTrace,
        formatTimestamp,
        renderTraceModal,
        closeTraceModal,
        copyTraceToClipboard,
        renderTimelineEvent,
        renderTypeBadge,
        escapeHtml,
        showTrace,
        TRACE_TYPE_CONFIG
    };
})();

// Make globally available
window.TraceViewer = TraceViewer;







