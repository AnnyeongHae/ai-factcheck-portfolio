#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/prompt_manager.py
=============================================================================
Centralized Prompt Repository and Lifecycle Manager (Prompt Registry)
- Discovers, validates, and manages all system and user prompts from configs/prompts/
- Provides unified Python interface for LLM calling tools (Gemini, OpenRouter, etc.)
- Supports prompt versioning, templating, parameter injection, and CLI inspection
=============================================================================
"""

import os
import sys
import json
import glob
from typing import Dict, List, Optional, Any

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import yaml
except ImportError:
    yaml = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, 'configs', 'prompts')


class PromptTemplate:
    """Represents a standardized, version-controlled prompt definition."""

    def __init__(self, raw_data: dict, file_path: str):
        self.raw = raw_data
        self.file_path = file_path
        
        meta = raw_data.get('meta', {})
        self.name = meta.get('name', os.path.splitext(os.path.basename(file_path))[0])
        self.version = meta.get('version', '1.0.0')
        self.description = meta.get('description', '')
        self.last_updated = meta.get('last_updated', '')

        params = raw_data.get('model_parameters', {})
        self.temperature = float(params.get('temperature', 0.2))
        self.response_mime_type = params.get('response_mime_type', 'application/json')
        self.top_p = params.get('top_p', None)
        self.max_tokens = params.get('max_tokens', None)

        self.persona_and_role = raw_data.get('persona_and_role', '').strip()
        self.system_instruction = raw_data.get('system_instruction', '').strip()
        self.output_json_schema = raw_data.get('output_json_schema', '').strip()
        self.classification_criteria = raw_data.get('classification_criteria', {})
        self.multilingual_guidelines = raw_data.get('multilingual_guidelines', {})

    def get_system_prompt(self) -> str:
        """Assembles the complete system prompt for LLM consumption."""
        parts = []
        base_role = self.persona_and_role or self.system_instruction
        if base_role:
            parts.append(base_role)
        if self.output_json_schema:
            parts.append(f"반드시 다음 JSON 규격으로만 응답해야 합니다:\n{self.output_json_schema}")
        return '\n\n'.join(parts)

    def render(self, **kwargs) -> str:
        """Renders template strings with dynamic variable replacement."""
        content = self.get_system_prompt()
        for k, v in kwargs.items():
            content = content.replace(f"{{{{{k}}}}}", str(v))
        return content

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'temperature': self.temperature,
            'response_mime_type': self.response_mime_type,
            'file_path': os.path.relpath(self.file_path, BASE_DIR),
            'has_schema': bool(self.output_json_schema),
        }


class PromptRegistry:
    """Central registry managing prompt discovery, caching, and resolution."""

    _prompts: Dict[str, PromptTemplate] = {}
    _aliases: Dict[str, str] = {
        'inbox': 'inbox_trilingual_enrichment',
        'inbox_enrichment': 'inbox_trilingual_enrichment',
        'enrichment': 'inbox_trilingual_enrichment',
        'inbox_enrichment_prompt': 'inbox_trilingual_enrichment',
        'dedup': 'semantic_tech_deduplication',
        'dedup_prompt': 'semantic_tech_deduplication',
        'deep_factcheck': 'deep_technical_factcheck_dossier',
        'factcheck': 'deep_technical_factcheck_dossier',
        'deep_factcheck_prompt': 'deep_technical_factcheck_dossier',
    }

    @classmethod
    def load_all(cls, directory: str = PROMPTS_DIR) -> Dict[str, PromptTemplate]:
        """Scans configs/prompts and registers all available YAML/JSON prompts."""
        cls._prompts.clear()
        if not os.path.exists(directory):
            return cls._prompts

        files = glob.glob(os.path.join(directory, '*.yaml')) + glob.glob(os.path.join(directory, '*.yml'))
        for fpath in sorted(files):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    if yaml:
                        data = yaml.safe_load(f)
                    else:
                        continue
                if isinstance(data, dict):
                    template = PromptTemplate(data, fpath)
                    cls._prompts[template.name] = template
                    fname_key = os.path.splitext(os.path.basename(fpath))[0]
                    cls._aliases[fname_key] = template.name
            except Exception as e:
                print(f"[!] Error loading prompt from {fpath}: {e}")

        return cls._prompts

    @classmethod
    def get(cls, name_or_alias: str) -> Optional[PromptTemplate]:
        """Retrieves a prompt template by canonical name or alias."""
        if not cls._prompts:
            cls.load_all()

        target_name = cls._aliases.get(name_or_alias, name_or_alias)
        if target_name in cls._prompts:
            return cls._prompts[target_name]

        for k, p in cls._prompts.items():
            if k.lower() == name_or_alias.lower() or name_or_alias.lower() in k.lower():
                return p

        return None

    @classmethod
    def list_prompts(cls) -> List[dict]:
        """Returns structured metadata of all registered prompts."""
        if not cls._prompts:
            cls.load_all()
        return [p.to_dict() for p in cls._prompts.values()]

    @classmethod
    def validate_all(cls) -> Dict[str, bool]:
        """Validates that all registered prompts satisfy essential schema rules."""
        if not cls._prompts:
            cls.load_all()
        results = {}
        for name, p in cls._prompts.items():
            valid = bool(p.name and p.version and (p.persona_and_role or p.system_instruction))
            results[name] = valid
        return results


def get_prompt(name_or_alias: str) -> Optional[PromptTemplate]:
    """Convenience function to get a prompt template."""
    return PromptRegistry.get(name_or_alias)


def cli_main():
    PromptRegistry.load_all()
    args = sys.argv[1:]

    if not args or args[0] in ('list', 'ls'):
        prompts = PromptRegistry.list_prompts()
        print(f"\n{'='*75}")
        print(f"📦 [Antigravity AI Prompt Repository] ({len(prompts)} Prompts Registered)")
        print(f"   Directory: {os.path.relpath(PROMPTS_DIR, BASE_DIR)}")
        print(f"{'='*75}")
        print(f"{'NAME':<35} | {'VERSION':<8} | {'TEMP':<5} | {'DESCRIPTION'}")
        print(f"{'-'*35}-+-{'-'*8}-+-{'-'*5}-+-{'-'*20}")
        for p in prompts:
            print(f"{p['name']:<35} | {p['version']:<8} | {p['temperature']:<5} | {p['description'][:40]}...")
        print(f"{'='*75}\n")

    elif args[0] in ('inspect', 'show', 'view'):
        if len(args) < 2:
            print("Usage: python tools/prompt_manager.py inspect <prompt_name>")
            return
        p = PromptRegistry.get(args[1])
        if not p:
            print(f"[-] Prompt '{args[1]}' not found in registry.")
            return
        print(f"\n{'='*75}")
        print(f"🔍 Inspecting Prompt: {p.name} (v{p.version})")
        print(f"   Path: {p.file_path}")
        print(f"   Temperature: {p.temperature} | MIME: {p.response_mime_type}")
        print(f"   Description: {p.description}")
        print(f"{'-'*75}")
        print("[System Prompt Generated]:\n")
        sp = p.get_system_prompt()
        print(sp[:800] + ('\n... [truncated]' if len(sp) > 800 else ''))
        print(f"\n{'='*75}\n")

    elif args[0] == 'validate':
        results = PromptRegistry.validate_all()
        print(f"\n{'='*50}")
        print("🛡️ Validating Prompt Integrity:")
        print(f"{'-'*50}")
        all_passed = True
        for name, passed in results.items():
            status = '✅ PASS' if passed else '❌ FAIL'
            print(f"  - {name:<35}: {status}")
            if not passed:
                all_passed = False
        print(f"{'-'*50}")
        print(f"Overall Result: {'All Prompts Valid!' if all_passed else 'Some Prompts Failed!'}")
        print(f"{'='*50}\n")


if __name__ == '__main__':
    cli_main()
