// frontend/pages/activitypub-test.js
import React, { useEffect, useState } from 'react';

export default function ActivityPubTestPage() {
  const [feedData, setFeedData] = useState([]);

  useEffect(() => {
    fetch('http://localhost:4000/universal-feed')
      .then(res => res.json())
      .then(data => {
        if (data.feed) {
          setFeedData(data.feed);
        }
      })
      .catch(err => console.error(err));
  }, []);

  const activitypubItems = feedData.filter(item => item.type === 'activitypub');

  return (
    <div style={{ padding: '20px' }}>
      <h1>ActivityPub Integration Test</h1>
      {activitypubItems.length === 0 && <p>No ActivityPub content found yet.</p>}
      {activitypubItems.map((item, index) => (
        <div key={index} style={{ border:'1px solid #ccc', marginBottom:'10px', padding:'10px' }}>
          <h3>Author: {item.author}</h3>
          <div 
            dangerouslySetInnerHTML={{ __html: item.content }} 
          />
          <small>Posted at: {new Date(item.createdAt).toLocaleString()}</small>
        </div>
      ))}
    </div>
  );
}
