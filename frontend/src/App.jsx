import { useEffect, useRef, useState } from 'react'
import { request } from './api.js'
import './App.css'

function Icon({ name, size = 20 }) {
  const paths = {
    book: <><path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1Z" /><path d="M12 6v14M6 8h3m6 0h3" /></>,
    upload: <path d="M12 16V4m-4 4 4-4 4 4M4 15v5h16v-5" />,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    check: <path d="m5 12 4 4L19 6" />,
    spark: <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z" />,
    image: <><rect x="3" y="3" width="18" height="18" rx="3" /><circle cx="8" cy="8" r="1.5" /><path d="m3 17 5-5 4 4 4-6 5 7" /></>,
    external: <path d="M14 3h7v7m0-7L10 14M10 3H4v17h17v-6" />,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function BookSpines() {
  return <div className="book-spines" aria-hidden="true">
    <div className="spine spine-olive"><span>THE ART OF DISCOVERY</span><i /></div>
    <div className="spine spine-sand"><i /><span>A new perspective</span></div>
    <div className="spine spine-clay"><span>ONE MORE CHAPTER</span><i /></div>
    <div className="spine spine-cream"><span>Small wonders</span></div>
    <div className="spine spine-forest"><i /><span>Between the lines</span></div>
  </div>
}

function StepTitle({ number, title, description, complete }) {
  return <div className="step-title">
    <span className={`step-number ${complete ? 'complete' : ''}`}>{complete ? <Icon name="check" size={16} /> : number}</span>
    <div><h2>{title}</h2><p>{description}</p></div>
  </div>
}

function libraryUrl(workId) {
  const match = String(workId || '').match(/^(?:\/works\/)?(OL\d+W)$/)
  return match ? `https://openlibrary.org/works/${match[1]}` : null
}

function DetectedBook({ book, index }) {
  const metadata = book.metadata || {}
  const matched = book.match_status === 'matched'
  const title = metadata.title || book.detected_title || 'Untitled book'
  const authors = metadata.authors?.length ? metadata.authors.join(', ') : book.detected_author || 'Author unknown'
  return <article className={`detected-book ${matched ? '' : 'unmatched'}`}>
    <div className={`mini-book tone-${index % 4}`} aria-hidden="true"><Icon name="book" size={23} /></div>
    <div className="book-details">
      <h3>{title}</h3><p className="author">{authors}</p>
      {metadata.description && <p className="book-description">{metadata.description}</p>}
      <span className={`match-label ${matched ? 'matched' : ''}`}>
        {matched && <Icon name="check" size={12} />}
        {matched ? 'Book details found' : book.match_status === 'api_error' ? 'Details temporarily unavailable' : 'No metadata found'}
      </span>
    </div>
  </article>
}

export default function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [dragging, setDragging] = useState(false)
  const [scan, setScan] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [preference, setPreference] = useState('')
  const [recommending, setRecommending] = useState(false)
  const [recommendationError, setRecommendationError] = useState('')
  const [recommendations, setRecommendations] = useState(null)
  const inputRef = useRef(null)
  const resultsRef = useRef(null)
  const busy = scanning || recommending

  useEffect(() => {
    if (!file) { setPreview(''); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  function chooseFile(selected) {
    if (busy || !selected) return
    setDragging(false)
    setUploadError('')
    if (!(selected.type === 'image/jpeg' || selected.type === 'image/png' || (!selected.type && /\.(jpe?g|png)$/i.test(selected.name)))) {
      setUploadError('Please choose a JPEG or PNG photo.'); return
    }
    if (selected.size === 0 || selected.size > 10 * 1024 * 1024) {
      setUploadError(selected.size === 0 ? 'This file is empty. Please choose another photo.' : 'This photo is too large. Choose one smaller than 10 MB.'); return
    }
    setFile(selected)
    setScan(null)
    setRecommendations(null)
    setRecommendationError('')
  }

  function startOver() {
    if (busy) return
    setFile(null); setScan(null); setPreference(''); setRecommendations(null)
    setUploadError(''); setRecommendationError(''); setDragging(false)
    if (inputRef.current) inputRef.current.value = ''
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function scanPhoto(event) {
    event.preventDefault()
    if (!file || busy || scan) return
    setScanning(true); setUploadError('')
    const body = new FormData()
    body.append('file', file)
    try {
      const data = await request('/scans', { method: 'POST', body })
      if (!Number.isInteger(data.scan_id) || !Array.isArray(data.books)) throw new Error('We couldn’t read the scan results. Please try again.')
      setScan(data)
    } catch (error) { setUploadError(error.message) }
    finally { setScanning(false) }
  }

  async function findRecommendations(event) {
    event.preventDefault()
    if (!scan || !preference.trim() || busy || !scan.total_matched) return
    setRecommending(true); setRecommendationError(''); setRecommendations(null)
    try {
      const data = await request(`/scans/${scan.scan_id}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preference_text: preference.trim(), top_k: 3 }),
      })
      if (!Array.isArray(data.recommendations)) throw new Error('We couldn’t read your recommendations. Please try again.')
      setRecommendations(data.recommendations)
    } catch (error) { setRecommendationError(error.message) }
    finally { setRecommending(false) }
  }

  useEffect(() => {
    if (recommendations) resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [recommendations])

  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header">
      <a className="brand" href="./" aria-label="Shelf Scanner home"><span className="brand-mark"><Icon name="book" size={25} /></span><span>shelf<span className="brand-light">scanner</span><span className="brand-period">.</span></span></a>
      <span className="header-note">A little curiosity. A great next read.</span>
      {file && <button className="text-button start-over" onClick={startOver} disabled={busy}>Start a new scan <Icon name="arrow" size={16} /></button>}
    </header>

    <main id="main">
      <section className="hero" aria-labelledby="hero-title">
        <div className="eyebrow"><span /> FOR THE LOVE OF FINDING BOOKS</div>
        <h1 id="hero-title">Your next read is hiding<br />in <em>plain sight.</em></h1>
        <p>A shelf full of possibilities. A photo to get started.<br className="desktop-break" /> Discover the books in front of you, then find the ones for you.</p>
        <div className="journey" aria-label="Three steps: scan, discover, find your next read"><span><b>01</b> Scan a shelf</span><i /><span><b>02</b> Discover the books</span><i /><span><b>03</b> Find your next read</span></div>
      </section>

      <div className="workspace">
        <div className="workflow">
          <section className="panel upload-panel" aria-labelledby="upload-title">
            <StepTitle number="01" title={<span id="upload-title">Start with a shelf</span>} description="Your next chapter starts with a photo." complete={!!scan} />
            <form onSubmit={scanPhoto}>
              <input ref={inputRef} className="visually-hidden" id="bookshelf-photo" type="file" accept="image/jpeg,image/png" disabled={busy} onChange={event => { chooseFile(event.target.files?.[0]); event.target.value = '' }} />
              <div className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-photo' : ''}`} onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]) }}>
                {preview ? <>
                  <img className="photo-preview" src={preview} alt="Your selected bookshelf" />
                  <div className="photo-caption"><span><Icon name="image" size={16} /><span>{file.name}</span></span><label className={`change-photo ${busy ? 'disabled' : ''}`} htmlFor="bookshelf-photo">Change photo</label></div>
                </> : <label className="drop-label" htmlFor="bookshelf-photo">
                  <span className="upload-symbol"><Icon name="upload" size={30} /></span>
                  <strong>Every shelf has a story.</strong>
                  <span>Drop your bookshelf photo here</span>
                  <span className="choose-photo">Choose a photo <Icon name="arrow" size={15} /></span>
                  <small>JPEG or PNG · Up to 10 MB / 20 MP</small>
                </label>}
              </div>
              {uploadError && <p className="error-message" role="alert">{uploadError}</p>}
              <div className="upload-actions"><p><Icon name="image" size={15} /> Clear spines make happy discoveries.</p><button className="primary-button" type="submit" disabled={!file || busy || !!scan}>{scanning ? <><span className="spinner" /> Scanning your shelf…</> : scan ? <><Icon name="check" size={17} /> Photo scanned</> : <>Scan bookshelf <Icon name="arrow" size={17} /></>}</button></div>
              <div className="loading-note" role="status" aria-live="polite">{scanning ? 'Reading book spines and looking up the details. This can take a little while.' : scan ? `Scan complete. ${scan.total_detected} books detected, ${scan.total_matched} matched.` : ''}</div>
            </form>
          </section>

          {scan && <section className="panel reveal" aria-labelledby="discovery-title">
            <StepTitle number="02" title={<span id="discovery-title">Meet your shelf</span>} description="A closer look at the stories in front of you." complete />
            <div className="discovery-summary"><span><strong>{scan.total_detected}</strong> detected</span><span><strong>{scan.total_matched}</strong> matched</span>{scan.total_unmatched > 0 && <span>{scan.total_unmatched} without a match</span>}</div>
            {scan.total_api_errors > 0 && <p className="notice" role="status">Some book details couldn’t be retrieved.{scan.total_matched > 0 ? ' You can still explore recommendations from the matched books.' : ' Please try scanning again in a moment.'}</p>}
            {scan.books.length ? <div className="detected-grid">{scan.books.map((book, index) => <DetectedBook key={`${book.book_id || book.detected_title}-${index}`} book={book} index={index} />)}</div> : <div className="empty-state"><Icon name="book" size={32} /><h3>No readable titles this time</h3><p>Try a closer, well-lit photo with book spines facing the camera.</p></div>}
            {!scan.total_matched && scan.books.length > 0 && <p className="notice">We found titles, but couldn’t match their details. Try a clearer photo to get recommendations.</p>}
          </section>}

          {scan && scan.total_matched > 0 && <section className="panel reveal" aria-labelledby="preference-title">
            <StepTitle number="03" title={<span id="preference-title">What speaks to you?</span>} description="Tell us what you love. We’ll find a place to start." complete={recommendations !== null} />
            <form onSubmit={findRecommendations}>
              <label className="field-label" htmlFor="preference">Your reading interests</label>
              <textarea id="preference" rows="4" maxLength={2000} value={preference} disabled={recommending} onChange={event => { setPreference(event.target.value); setRecommendations(null); setRecommendationError('') }} placeholder="I love science fiction, psychology, and thoughtful stories that stay with me…" aria-describedby="preference-hint" required />
              <div className="preference-footer"><p id="preference-hint">A favorite genre, a mood, a topic. Make it yours.</p><span>{preference.length}/2000</span></div>
              {recommendationError && <p className="error-message" role="alert">{recommendationError}</p>}
              <button className="primary-button recommendation-button" disabled={!preference.trim() || busy} type="submit">{recommending ? <><span className="spinner" /> Finding your next read…</> : <><Icon name="spark" size={17} /> Find my next read <Icon name="arrow" size={17} /></>}</button>
              <div role="status" className="loading-note">{recommending ? 'Finding the books that connect with your interests…' : ''}</div>
            </form>
          </section>}

          {recommendations !== null && <section className="recommendations-section reveal" ref={resultsRef} aria-labelledby="recommendation-title" tabIndex={-1}>
            <div className="eyebrow"><Icon name="spark" size={16} /> A FEW GOOD PLACES TO START</div>
            <h2 id="recommendation-title">Your next chapter awaits.</h2>
            <p className="results-intro">Picked from your shelf, with your interests in mind.</p>
            <div className="recommendation-list">{recommendations.map((book, index) => {
              const metadata = scan.books.find(item => item.book_id === book.book_id)?.metadata || {}
              const url = libraryUrl(book.work_id)
              return <article className={`recommendation-card ${index === 0 ? 'first-pick' : ''}`} key={book.book_id || `${book.title}-${index}`}>
                <div className="pick-number">0{index + 1}</div><div className="pick-content">
                  {index === 0 && <span className="top-pick"><Icon name="spark" size={12} /> YOUR FIRST PICK</span>}
                  <h3>{book.title || 'Untitled book'}</h3><p className="author">{book.authors?.join(', ') || 'Author unknown'}</p>
                  {metadata.description && <p className="pick-description">{metadata.description}</p>}
                  {metadata.subjects?.length > 0 && <div className="subjects">{metadata.subjects.slice(0, 3).map(subject => <span key={subject}>{subject}</span>)}</div>}
                  {url && <a className="book-link" href={url} target="_blank" rel="noreferrer">Explore on Open Library <Icon name="external" size={13} /></a>}
                </div>
              </article>
            })}</div>
            {recommendations.length === 0 && <div className="empty-state"><Icon name="book" size={30} /><h3>No recommendations this time</h3><p>Try another preference or a photo with more matched books.</p></div>}
            <p className="closing-note">Sometimes the best discoveries are right in front of you.</p>
          </section>}
        </div>

        <aside className="shelf-aside" aria-label="Tips for your scan">
          <div className="aside-tag"><Icon name="spark" size={15} /> A LITTLE SHELF HELP</div>
          <h2>So many spines.<br /><em>One good beginning.</em></h2>
          <p>In a bookshop, at a book fair, or beside your own collection. Let curiosity lead the way.</p>
          <div className="aside-rule" />
          <h3>A photo worth a thousand pages</h3>
          <ul className="photo-tips"><li><Icon name="check" size={15} /> Keep titles clear and in focus</li><li><Icon name="check" size={15} /> Find a little natural light</li><li><Icon name="check" size={15} /> Aim straight at the book spines</li></ul>
          <BookSpines />
          <p className="aside-footnote">A whole world between the covers.</p>
        </aside>
      </div>
    </main>
    <footer className="site-footer"><span><Icon name="book" size={17} /> Made for curious readers.</span><span>One shelf. Endless possibilities.</span></footer>
  </>
}
