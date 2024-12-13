// frontend/pages/universal-feed-translated.js
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function UniversalFeedTranslatedPage() {
  const router = useRouter();
  const [feedData, setFeedData] = useState([]);
  const [lang, setLang] = useState(router.query.lang || '');

  useEffect(() => {
    const queryParam = lang ? `?lang=${lang}` : '';
    fetch(`http://localhost:4000/universal-feed${queryParam}`)
      .then(res => res.json())
      .then(data => {
        if (data.feed) {
          setFeedData(data.feed);
        }
      })
      .catch(err => console.error(err));
  }, [lang]);

  const handleLanguageChange = (e) => {
    setLang(e.target.value);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Universal Feed (Translated)</h1>
      <p>Choose a language to translate content:</p>
      <select value={lang} onChange={handleLanguageChange}>
        <option value="">Original</option>
        <option value="ja">Japanese</option>
        <option value="en">English</option>
        <option value="fr">French</option>
        <option value="es">Spanish</option>
        <option value="de">German</option>
      </select>
      <ul style={{ marginTop: '20px' }}>
        {feedData.map((item, index) => {
          return (
            <li key={index} style={{ marginBottom: '15px' }}>
              <strong>Type:</strong> {item.type}<br />
              <strong>Author:</strong> {item.author}<br />
              {item.title && <div><strong>Title:</strong> {item.title}</div>}
              {item.content && <div><strong>Content:</strong> {item.content}</div>}
              {item.body && <div><strong>Body:</strong> {item.body}</div>}
              <small>Posted at: {new Date(item.createdAt).toLocaleString()}</small>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
