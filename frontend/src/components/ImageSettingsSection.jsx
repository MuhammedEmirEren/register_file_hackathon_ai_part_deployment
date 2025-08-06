import React from 'react';
import BackgroundGenerationElement from './BackgroundGenerationElement';
import ImageShowcaseModal from './ImageShowcaseModal';

const ImageSettingsSection = ({ 
  currentImage, 
  settings, 
  onSettingChange, 
  onEnhance 
}) => {
  const [showGeneration, setShowGeneration] = React.useState(false);
  const [modalImage, setModalImage] = React.useState(null);
  const [modalTitle, setModalTitle] = React.useState('');

  const showGenerationPanel = (show) => {
    setShowGeneration(show);
  };

  const closeGenerationPanel = () => {
    setShowGeneration(false);
  };

  const handleGeneratedBackground = (backgroundData) => {
    // backgroundData contains: 
    // { background_id, background_base64, background_public_url, background_file_name, background_file_path }
    console.log('Generated background data:', backgroundData);
    console.log('File path:', backgroundData.background_file_path);
    console.log('Public URL:', backgroundData.background_public_url);
    console.log('File name:', backgroundData.background_file_name);
    
    // Update the settings with the generated background
    onSettingChange({
      ...settings,
      generatedBackground: backgroundData
    });
    
    // Close the generation panel
    setShowGeneration(false);
  };

  const toggleSetting = (setting) => {
    onSettingChange({
      ...settings,
      [setting]: !settings[setting]
    });
  };

  const handleImageClick = (imageSrc, title) => {
    setModalImage(imageSrc);
    setModalTitle(title);
  };

  const closeModal = () => {
    setModalImage(null);
    setModalTitle('');
  };

  const handleBackgroundImageClick = (imagePath) => {
    // Check if the image source is already a base64 data URL (for generated images)
    if (imagePath.src.startsWith('data:')) {
      // It's already a base64 data URL, no need to fetch
      onSettingChange({
        ...settings,
        background: {background_id: imagePath.id, background_base64: imagePath.src}
      });
      console.log('Background image set (base64):', imagePath.src);
      return;
    }
    
    //convert imagepath to base64 to give backend
    fetch(imagePath.src)
      .then(response => response.blob())
      .then(blob => {
        const reader = new FileReader();
        reader.onloadend = () => {
          onSettingChange({
            ...settings,
            background: {background_id: imagePath.id, background_base64: reader.result}
          });
        };
        reader.readAsDataURL(blob);
        console.log('Background image set:', reader.result);
        console.log('Settings updated:', {settings});
      })
      .catch(error => {
        console.error('Error loading background image:', error);
      });
  };

  const sampleImages = [
    {
      id: 1,
      src: '/bg_1.jpeg',
      alt: 'Sample Background 1'
    },
    {
      id: 2,
      src: '/bg_2.jpeg',
      alt: 'Sample Background 2'
    },
    {
      id: 3,
      src: '/bg_3.jpg',
      alt: 'Sample Background 3'
    },
    {id: 4,
      src: '/bg_4.jpg',
      alt: 'Sample Background 4'
    },
    {
      id: 5,
      src: settings.generatedBackground?.background_base64 || '/bg_5.jpg',
      alt: 'Sample Background 5'
    },
  ];

  return (
    <section className="image-settings-section">
      <div className="image-settings-container">
        <div className="image-panel">
          <h3>🖼️ Original Image</h3>
          <div className="image-display" onClick={() => handleImageClick(currentImage, 'Original Image')}>
            <img src={currentImage} alt="Original" 
            />
          </div>
          <div className="image-info">
            <span>📏 Image loaded</span>
          </div>
        </div>
        
        <div className="settings-panel">
          <h3>⚙️ Choose Settings</h3>
          <div className="settings-options">
            <div className="setting-item">
              <label>Background: </label>
              <div className="sample-images-grid">
                {sampleImages.map((image) => (
                  <div 
                    key={image.id}
                    className={`sample-image-card ${settings.background?.background_id === image.id || (settings.background?.background_id === 'ai_generated' && image.id === 5) ? 'selected' : ''}`}
                    onClick={() => handleBackgroundImageClick(image)}
                  >
                    <div className="sample-image-container">
                      <img 
                        src={image.src} 
                        alt={image.alt}
                        className="sample-image"
                      />
                    </div>
                  </div>
                ))}
                <div className="sample-image-card ai-option" onClick={() => showGenerationPanel(true)}>
                  <div className="sample-image-container ai-container">
                    <div className="ai-icon">
                      🤖
                    </div>
                    <span className="ai-label">Generate With AI</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="setting-item">
              <label>Title Generation</label>
              <input 
                type="checkbox" 
                checked={settings.titleGeneration}
                onChange={() => toggleSetting('titleGeneration')}
              />
            </div>
            
            <div className="setting-item">
              <label>Description Generation</label>
              <input 
                type="checkbox" 
                checked={settings.descriptionGeneration}
                onChange={() => toggleSetting('descriptionGeneration')}
              />
            </div>
          </div>
          
          <button className="enhance-btn" onClick={onEnhance}>
            ✨ Enhance
          </button>
        </div>
      </div>
      {showGeneration && (
      <BackgroundGenerationElement
        onClose={closeGenerationPanel}
        onBackgroundGenerated={handleGeneratedBackground}
      />
      )}
      {modalImage && (
      <ImageShowcaseModal
        selectedImage={modalImage}
        onCancel ={closeModal}
      />
      )}
    </section>
  );
};

export default ImageSettingsSection; 