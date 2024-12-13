// frontend/pages/global-feed.js
import React, { useEffect, useState } from 'react';

export default function GlobalFeedPage() {
  const [feedData, setFeedData] = useState([]);

  useEffect(() => {
    // ※ 実際にはCORS対応やプロキシ等が必要になる場合がある
    fetch('http://localhost:4000/universal-feed')
      .then(res => res.json())
      .then(data => {
        if (data.feed) {
          setFeedData(data.feed);
        }
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>Global Feed (Universal Content)</h1>
      <ul>
        {feedData.map((item, index) => {
          if (item.type === 'local_tweet') {
            return (
              <li key={index}>
                <strong>Local Tweet by {item.author?.displayName || item.author?.username}:</strong> {item.content}
                <br />
                <small>At {new Date(item.createdAt).toLocaleString()}</small>
              </li>
            );
          } else if (item.type === 'external') {
            return (
              <li key={index}>
                <strong>External Content:</strong> {item.title}
                <br />
                {item.body}
              </li>
            );
          }
          return <li key={index}>Unknown content</li>;
        })}
      </ul>
    </div>
  );
}
