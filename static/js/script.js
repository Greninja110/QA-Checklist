/**
 * QA Testing Checklist Application
 * Frontend JavaScript
 */

// Global state
let currentSession = null;
let currentHeadingId = null;
let editingHeadingId = null;
let editingItemId = null;
let editingItemHeadingId = null;
let editingNoteId = null;

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('QA Testing Checklist App initialized');
    initTheme();
    loadSession();
    initializeEventListeners();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.querySelector('.theme-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

// Initialize event listeners
function initializeEventListeners() {
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Session info
    document.getElementById('save-session-info').addEventListener('click', saveSessionInfo);
    
    // Add buttons
    document.getElementById('add-heading-btn').addEventListener('click', () => openHeadingModal());
    document.getElementById('add-note-btn').addEventListener('click', () => openNoteModal());
    
    // Modal buttons - Heading
    document.getElementById('save-heading-btn').addEventListener('click', saveHeading);
    document.getElementById('cancel-heading-btn').addEventListener('click', closeHeadingModal);
    
    // Modal buttons - Item
    document.getElementById('save-item-btn').addEventListener('click', saveItem);
    document.getElementById('cancel-item-btn').addEventListener('click', closeItemModal);
    
    // Modal buttons - Note
    document.getElementById('save-note-btn').addEventListener('click', saveNote);
    document.getElementById('cancel-note-btn').addEventListener('click', closeNoteModal);
    
    // Action buttons
    document.getElementById('complete-btn').addEventListener('click', completeSession);
    document.getElementById('reset-btn').addEventListener('click', resetSession);
    
    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
    
    // Enter key handlers
    document.getElementById('heading-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveHeading();
    });
    
    document.getElementById('item-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveItem();
    });
}

// Load session data from server
async function loadSession() {
    try {
        const response = await fetch('/api/session');
        if (!response.ok) throw new Error('Failed to load session');
        
        currentSession = await response.json();
        console.log('Session loaded:', currentSession);
        
        // Update UI
        document.getElementById('target-website').value = currentSession.target_website || '';
        document.getElementById('start-date').value = currentSession.start_date || '';
        
        renderChecklist();
        renderNotes();
    } catch (error) {
        console.error('Error loading session:', error);
        showError('Failed to load session. Please refresh the page.');
    }
}

// Save session info (target website and start date)
async function saveSessionInfo() {
    const targetWebsite = document.getElementById('target-website').value.trim();
    const startDate = document.getElementById('start-date').value;
    
    if (!targetWebsite) {
        showError('Please enter a target website.');
        return;
    }
    
    if (!startDate) {
        showError('Please select a start date.');
        return;
    }
    
    try {
        const response = await fetch('/api/session/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_website: targetWebsite, start_date: startDate })
        });
        
        if (!response.ok) throw new Error('Failed to save session info');
        
        const data = await response.json();
        currentSession = data.data;
        
        showSuccess('Session info saved!');
    } catch (error) {
        console.error('Error saving session info:', error);
        showError('Failed to save session info. Please try again.');
    }
}

// Render checklist
function renderChecklist() {
    const container = document.getElementById('checklist-container');
    
    if (!currentSession.checklist || currentSession.checklist.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No checklist items yet. Add a heading to get started.</p></div>';
        return;
    }
    
    container.innerHTML = currentSession.checklist.map((heading, index) => `
        <div class="checklist-heading" data-heading-id="${heading.id}">
            <div class="heading-header">
                <div class="heading-title">
                    <span class="heading-number">${index + 1}.</span> ${escapeHtml(heading.title)}
                </div>
                <div class="heading-actions">
                    <button class="btn-icon" onclick="openItemModal(${heading.id})" title="Add Sub-item">➕</button>
                    <button class="btn-icon" onclick="openHeadingModal(${heading.id})" title="Edit Heading">✏️</button>
                    <button class="btn-icon btn-delete" onclick="deleteHeading(${heading.id})" title="Delete Heading">🗑️</button>
                </div>
            </div>
            <div class="heading-items">
                ${heading.items.length > 0 ? heading.items.map(item => `
                    <div class="checklist-item">
                        <input 
                            type="checkbox" 
                            ${item.checked ? 'checked' : ''}
                            onchange="toggleItem(${heading.id}, ${item.id}, this.checked)"
                        >
                        <span class="item-text ${item.checked ? 'checked' : ''}">${escapeHtml(item.text)}</span>
                        <div class="item-actions">
                            <button class="btn-icon" onclick="openItemModal(${heading.id}, ${item.id})" title="Edit">✏️</button>
                            <button class="btn-icon btn-delete" onclick="deleteItem(${heading.id}, ${item.id})" title="Delete">🗑️</button>
                        </div>
                    </div>
                `).join('') : '<p style="color: var(--text-secondary); padding: 10px;">No items yet. Click ➕ to add sub-items.</p>'}
            </div>
        </div>
    `).join('');
}

// Render notes
function renderNotes() {
    const container = document.getElementById('notes-container');
    
    if (!currentSession.notes || currentSession.notes.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No notes yet. Click "Add Note" to create one.</p></div>';
        return;
    }
    
    container.innerHTML = currentSession.notes.map(note => `
        <div class="note-item">
            <div class="note-text">${escapeHtml(note.text)}</div>
            <div class="note-footer">
                <span class="note-time">${note.created_at || ''}</span>
                <div class="note-actions">
                    <button class="btn-icon" onclick="openNoteModal(${note.id})" title="Edit">✏️</button>
                    <button class="btn-icon btn-delete" onclick="deleteNote(${note.id})" title="Delete">🗑️</button>
                </div>
            </div>
        </div>
    `).join('');
}

// Toggle checklist item
async function toggleItem(headingId, itemId, checked) {
    try {
        const response = await fetch('/api/checklist/item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ heading_id: headingId, item_id: itemId, checked })
        });
        
        if (!response.ok) throw new Error('Failed to toggle item');
        
        // Update local state
        const heading = currentSession.checklist.find(h => h.id === headingId);
        if (heading) {
            const item = heading.items.find(i => i.id === itemId);
            if (item) {
                item.checked = checked;
                renderChecklist();
            }
        }
    } catch (error) {
        console.error('Error toggling item:', error);
        showError('Failed to update item. Please try again.');
    }
}

// Heading Modal
function openHeadingModal(headingId = null) {
    editingHeadingId = headingId;
    const modal = document.getElementById('heading-modal');
    const input = document.getElementById('heading-input');
    const title = document.getElementById('heading-modal-title');
    
    if (headingId) {
        const heading = currentSession.checklist.find(h => h.id === headingId);
        if (heading) {
            input.value = heading.title;
            title.textContent = 'Edit Heading';
        }
    } else {
        input.value = '';
        title.textContent = 'Add Heading';
    }
    
    modal.style.display = 'flex';
    input.focus();
}

function closeHeadingModal() {
    document.getElementById('heading-modal').style.display = 'none';
    editingHeadingId = null;
}

async function saveHeading() {
    const input = document.getElementById('heading-input');
    const title = input.value.trim();
    
    if (!title) {
        showError('Please enter a heading title.');
        return;
    }
    
    try {
        let response;
        
        if (editingHeadingId) {
            // Edit existing heading
            response = await fetch(`/api/checklist/heading/${editingHeadingId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });
        } else {
            // Add new heading
            response = await fetch('/api/checklist/heading', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });
        }
        
        if (!response.ok) throw new Error('Failed to save heading');
        
        closeHeadingModal();
        await loadSession();
        showSuccess(editingHeadingId ? 'Heading updated!' : 'Heading added!');
    } catch (error) {
        console.error('Error saving heading:', error);
        showError('Failed to save heading. Please try again.');
    }
}

async function deleteHeading(headingId) {
    if (!confirm('Are you sure you want to delete this heading and all its items?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/checklist/heading/${headingId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete heading');
        
        await loadSession();
        showSuccess('Heading deleted!');
    } catch (error) {
        console.error('Error deleting heading:', error);
        showError('Failed to delete heading. Please try again.');
    }
}

// Item Modal
function openItemModal(headingId, itemId = null) {
    currentHeadingId = headingId;
    editingItemId = itemId;
    editingItemHeadingId = headingId;
    
    const modal = document.getElementById('item-modal');
    const input = document.getElementById('item-input');
    const title = document.getElementById('item-modal-title');
    
    if (itemId) {
        const heading = currentSession.checklist.find(h => h.id === headingId);
        if (heading) {
            const item = heading.items.find(i => i.id === itemId);
            if (item) {
                input.value = item.text;
                title.textContent = 'Edit Sub-item';
            }
        }
    } else {
        input.value = '';
        title.textContent = 'Add Sub-item';
    }
    
    modal.style.display = 'flex';
    input.focus();
}

function closeItemModal() {
    document.getElementById('item-modal').style.display = 'none';
    currentHeadingId = null;
    editingItemId = null;
    editingItemHeadingId = null;
}

async function saveItem() {
    const input = document.getElementById('item-input');
    const text = input.value.trim();
    
    if (!text) {
        showError('Please enter item text.');
        return;
    }
    
    try {
        let response;
        
        if (editingItemId) {
            // Edit existing item
            response = await fetch(`/api/checklist/item/${editingItemHeadingId}/${editingItemId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
        } else {
            // Add new item
            response = await fetch('/api/checklist/item', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ heading_id: currentHeadingId, text })
            });
        }
        
        if (!response.ok) throw new Error('Failed to save item');
        
        closeItemModal();
        await loadSession();
        showSuccess(editingItemId ? 'Item updated!' : 'Item added!');
    } catch (error) {
        console.error('Error saving item:', error);
        showError('Failed to save item. Please try again.');
    }
}

async function deleteItem(headingId, itemId) {
    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/checklist/item/${headingId}/${itemId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete item');
        
        await loadSession();
        showSuccess('Item deleted!');
    } catch (error) {
        console.error('Error deleting item:', error);
        showError('Failed to delete item. Please try again.');
    }
}

// Note Modal
function openNoteModal(noteId = null) {
    editingNoteId = noteId;
    const modal = document.getElementById('note-modal');
    const input = document.getElementById('note-input');
    const title = document.getElementById('note-modal-title');
    
    if (noteId) {
        const note = currentSession.notes.find(n => n.id === noteId);
        if (note) {
            input.value = note.text;
            title.textContent = 'Edit Note';
        }
    } else {
        input.value = '';
        title.textContent = 'Add Note';
    }
    
    modal.style.display = 'flex';
    input.focus();
}

function closeNoteModal() {
    document.getElementById('note-modal').style.display = 'none';
    editingNoteId = null;
}

async function saveNote() {
    const input = document.getElementById('note-input');
    const text = input.value.trim();
    
    if (!text) {
        showError('Please enter note text.');
        return;
    }
    
    try {
        let response;
        
        if (editingNoteId) {
            // Edit existing note
            response = await fetch(`/api/notes/${editingNoteId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
        } else {
            // Add new note
            response = await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
        }
        
        if (!response.ok) throw new Error('Failed to save note');
        
        closeNoteModal();
        await loadSession();
        showSuccess(editingNoteId ? 'Note updated!' : 'Note added!');
    } catch (error) {
        console.error('Error saving note:', error);
        showError('Failed to save note. Please try again.');
    }
}

async function deleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete note');
        
        await loadSession();
        showSuccess('Note deleted!');
    } catch (error) {
        console.error('Error deleting note:', error);
        showError('Failed to delete note. Please try again.');
    }
}

// Complete session
async function completeSession() {
    if (!currentSession.target_website) {
        showError('Please enter a target website before completing.');
        return;
    }
    
    if (!currentSession.start_date) {
        showError('Please select a start date before completing.');
        return;
    }
    
    const endDate = new Date().toISOString().split('T')[0];
    
    if (!confirm(`Complete testing for "${currentSession.target_website}"? This will save the session to history and reset the checklist.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/session/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ end_date: endDate })
        });
        
        if (!response.ok) throw new Error('Failed to complete session');
        
        showSuccess('Session completed! View it in the History page.');
        await loadSession();
    } catch (error) {
        console.error('Error completing session:', error);
        showError('Failed to complete session. Please try again.');
    }
}

// Reset session
async function resetSession() {
    if (!confirm('Are you sure you want to reset the session? All current data will be lost unless you complete it first.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/session/reset', {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to reset session');
        
        showSuccess('Session reset successfully!');
        await loadSession();
    } catch (error) {
        console.error('Error resetting session:', error);
        showError('Failed to reset session. Please try again.');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    // Simple alert for now - you can enhance this with a toast notification
    console.log('Success:', message);
    alert(message);
}

function showError(message) {
    console.error('Error:', message);
    alert('Error: ' + message);
}

// Debug logging
console.log('QA Testing Checklist - Script loaded successfully');