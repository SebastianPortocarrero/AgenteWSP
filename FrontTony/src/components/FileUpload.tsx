import React, { useState, useRef } from 'react';
import { Paperclip, Image, FileText, X, Upload, Camera } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File, type: 'image' | 'document' | 'other') => void;
  onClose: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, onClose }) => {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    const file = files[0];
    const fileType = getFileType(file);
    onFileSelect(file, fileType);
    onClose();
  };

  const getFileType = (file: File): 'image' | 'document' | 'other' => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.includes('pdf') || file.type.includes('document') || file.type.includes('text')) return 'document';
    return 'other';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const uploadOptions = [
    {
      id: 'image',
      icon: Image,
      title: 'Imagen',
      description: 'JPG, PNG, GIF',
      color: 'text-blue-600 bg-blue-50 hover:bg-blue-100',
      accept: 'image/*',
      inputRef: imageInputRef
    },
    {
      id: 'document',
      icon: FileText,
      title: 'Documento',
      description: 'PDF, DOC, TXT',
      color: 'text-green-600 bg-green-50 hover:bg-green-100',
      accept: '.pdf,.doc,.docx,.txt,.xlsx,.xls',
      inputRef: fileInputRef
    },
    {
      id: 'camera',
      icon: Camera,
      title: 'Cámara',
      description: 'Tomar foto',
      color: 'text-purple-600 bg-purple-50 hover:bg-purple-100',
      accept: 'image/*',
      capture: true
    }
  ];

  return (
    <div className="absolute bottom-full left-0 mb-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 w-80">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        <h3 className="font-medium text-gray-900 dark:text-gray-100">Adjuntar archivo</h3>
        <button
          onClick={onClose}
          title="Cerrar selector de archivos"
          className="p-1 hover:bg-gray-100 rounded-full transition-colors"
        >
          <X className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Opciones de upload */}
      <div className="p-4 space-y-3">
        {uploadOptions.map((option) => {
          const IconComponent = option.icon;
          return (
            <button
              key={option.id}
              onClick={() => {
                if (option.inputRef) {
                  option.inputRef.current?.click();
                } else if (option.capture) {
                  // Para la cámara, crear un input temporal
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.accept = option.accept;
                  input.capture = 'environment';
                  input.onchange = (e) => {
                    const files = (e.target as HTMLInputElement).files;
                    handleFileSelect(files);
                  };
                  input.click();
                }
              }}
              className={`w-full flex items-center space-x-3 p-3 rounded-lg border border-gray-200 transition-colors ${option.color}`}
            >
              <div className="p-2 rounded-full bg-current bg-opacity-20">
                <IconComponent className="w-5 h-5" />
              </div>
              <div className="flex-1 text-left">
                <div className="font-medium text-gray-900">{option.title}</div>
                <div className="text-sm text-gray-500">{option.description}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Área de drag & drop */}
      <div
        className={`m-4 mt-0 border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragOver 
            ? 'border-green-400 bg-green-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600 font-medium">
          Arrastra archivos aquí
        </p>
        <p className="text-xs text-gray-500 mt-1">
          o usa las opciones de arriba
        </p>
      </div>

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.doc,.docx,.txt,.xlsx,.xls"
        title="Seleccionar documento"
        onChange={(e) => handleFileSelect(e.target.files)}
      />
      <input
        ref={imageInputRef}
        type="file"
        className="hidden"
        accept="image/*"
        title="Seleccionar imagen"
        onChange={(e) => handleFileSelect(e.target.files)}
      />
    </div>
  );
};

export default FileUpload; 