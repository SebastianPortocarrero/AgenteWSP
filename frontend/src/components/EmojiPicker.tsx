import { FC } from 'react';
// @ts-ignore - emoji-mart tiene problemas de tipos en esta versión
import data from '@emoji-mart/data';
// @ts-ignore - emoji-mart tiene problemas de tipos en esta versión
import Picker from '@emoji-mart/react';

interface EmojiPickerProps {
  onEmojiSelect: (emoji: string) => void;
  onClose: () => void;
}

const EmojiPicker: FC<EmojiPickerProps> = ({ onEmojiSelect, onClose }) => {
  const handleEmojiSelect = (emoji: any) => {
    // Extraer el emoji nativo del objeto de emoji-mart
    onEmojiSelect(emoji.native);
    onClose();
  };

  return (
    <div className="absolute bottom-full right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-[9999]">
      <Picker
        data={data}
        onEmojiSelect={handleEmojiSelect}
        onClickOutside={onClose}
        locale="es"
        theme="light"
        set="native"
        previewPosition="none"
        skinTonePosition="search"
        searchPosition="sticky"
        maxFrequentRows={2}
        perLine={8}
        emojiSize={20}
        emojiButtonSize={32}
        emojiButtonRadius="8px"
        emojiButtonColors={['#25D366']}
        autoFocus={false}
        categories={[
          'frequent',
          'people',
          'nature',
          'foods',
          'activity',
          'places',
          'objects',
          'symbols',
          'flags'
        ]}
      />
    </div>
  );
};

export default EmojiPicker; 