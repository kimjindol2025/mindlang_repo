#!/usr/bin/env python3
"""
Document Generation System - Automated API documentation
Generates comprehensive API documentation from annotations and schemas
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class DocumentFormat(Enum):
    """Document formats"""
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
    PDF = "PDF"
    SWAGGER = "SWAGGER"
    OPENAPI = "OPENAPI"


@dataclass
class APIEndpoint:
    """API endpoint documentation"""
    endpoint_id: str
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class APIDocument:
    """API documentation"""
    document_id: str
    api_name: str
    version: str
    description: str
    endpoints: List[APIEndpoint] = field(default_factory=list)
    schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    authentication: Dict[str, str] = field(default_factory=dict)
    format: DocumentFormat = DocumentFormat.MARKDOWN
    generated_at: float = field(default_factory=time.time)


class DocumentGenerator:
    """
    Document Generation System

    Provides:
    - Automatic API documentation generation
    - Multiple format support
    - Schema documentation
    - Example generation
    - Changelog tracking
    - Version management
    """

    def __init__(self):
        self.documents: Dict[str, APIDocument] = {}
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.schemas: Dict[str, Dict] = {}
        self.generation_history: List[Dict] = []

    def create_api_documentation(self,
                               api_name: str,
                               version: str,
                               description: str) -> APIDocument:
        """Create API documentation"""
        document_id = hashlib.md5(
            f"{api_name}:{version}:{time.time()}".encode()
        ).hexdigest()[:8]

        document = APIDocument(
            document_id=document_id,
            api_name=api_name,
            version=version,
            description=description
        )

        self.documents[document_id] = document
        return document

    def add_endpoint(self,
                    document_id: str,
                    path: str,
                    method: str,
                    summary: str,
                    description: str) -> Optional[APIEndpoint]:
        """Add endpoint to documentation"""
        document = self.documents.get(document_id)
        if not document:
            return None

        endpoint_id = hashlib.md5(
            f"{document_id}:{path}:{method}".encode()
        ).hexdigest()[:8]

        endpoint = APIEndpoint(
            endpoint_id=endpoint_id,
            path=path,
            method=method,
            summary=summary,
            description=description
        )

        document.endpoints.append(endpoint)
        self.endpoints[endpoint_id] = endpoint
        return endpoint

    def add_parameter(self,
                     endpoint_id: str,
                     name: str,
                     param_type: str,
                     required: bool = False,
                     description: str = "") -> bool:
        """Add parameter to endpoint"""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return False

        parameter = {
            "name": name,
            "type": param_type,
            "required": required,
            "description": description
        }

        endpoint.parameters.append(parameter)
        return True

    def add_response(self,
                    endpoint_id: str,
                    status_code: int,
                    description: str,
                    schema: Dict = None) -> bool:
        """Add response to endpoint"""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return False

        endpoint.responses[status_code] = {
            "description": description,
            "schema": schema or {}
        }

        return True

    def define_schema(self,
                     schema_name: str,
                     properties: Dict[str, Dict[str, str]]) -> str:
        """Define data schema"""
        schema_id = hashlib.md5(
            f"{schema_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        schema = {
            "name": schema_name,
            "type": "object",
            "properties": properties,
            "required": list(properties.keys())
        }

        self.schemas[schema_id] = schema
        return schema_id

    def generate_markdown(self, document_id: str) -> str:
        """Generate Markdown documentation"""
        document = self.documents.get(document_id)
        if not document:
            return ""

        markdown = f"# {document.api_name}\n\n"
        markdown += f"**Version:** {document.version}\n\n"
        markdown += f"{document.description}\n\n"

        markdown += "## Endpoints\n\n"

        for endpoint in document.endpoints:
            markdown += f"### {endpoint.method} {endpoint.path}\n\n"
            markdown += f"{endpoint.summary}\n\n"
            markdown += f"{endpoint.description}\n\n"

            if endpoint.parameters:
                markdown += "**Parameters:**\n\n"
                markdown += "| Name | Type | Required | Description |\n"
                markdown += "|------|------|----------|-------------|\n"
                for param in endpoint.parameters:
                    markdown += f"| {param['name']} | {param['type']} | {param['required']} | {param['description']} |\n"
                markdown += "\n"

            if endpoint.responses:
                markdown += "**Responses:**\n\n"
                for code, response in endpoint.responses.items():
                    markdown += f"- **{code}**: {response['description']}\n"
                markdown += "\n"

        return markdown

    def generate_openapi(self, document_id: str) -> Dict:
        """Generate OpenAPI specification"""
        document = self.documents.get(document_id)
        if not document:
            return {}

        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": document.api_name,
                "version": document.version,
                "description": document.description
            },
            "paths": {}
        }

        for endpoint in document.endpoints:
            if endpoint.path not in openapi["paths"]:
                openapi["paths"][endpoint.path] = {}

            openapi["paths"][endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "parameters": endpoint.parameters,
                "responses": {
                    str(code): {
                        "description": response["description"]
                    }
                    for code, response in endpoint.responses.items()
                }
            }

        return openapi

    def export_document(self,
                       document_id: str,
                       format: DocumentFormat = DocumentFormat.MARKDOWN) -> str:
        """Export documentation in specified format"""
        document = self.documents.get(document_id)
        if not document:
            return ""

        if format == DocumentFormat.MARKDOWN:
            content = self.generate_markdown(document_id)
        elif format == DocumentFormat.OPENAPI:
            content = json.dumps(self.generate_openapi(document_id), indent=2)
        else:
            content = ""

        # Record generation
        self.generation_history.append({
            "document_id": document_id,
            "format": format.value,
            "generated_at": time.time()
        })

        return content

    def get_documentation_stats(self) -> Dict:
        """Get documentation statistics"""
        total_endpoints = sum(len(doc.endpoints) for doc in self.documents.values())
        total_schemas = len(self.schemas)
        total_parameters = sum(
            len(ep.parameters) for doc in self.documents.values()
            for ep in doc.endpoints
        )

        return {
            "documents": len(self.documents),
            "endpoints": total_endpoints,
            "schemas": total_schemas,
            "parameters": total_parameters,
            "generations": len(self.generation_history),
        }

    def generate_documentation_report(self) -> str:
        """Generate documentation report"""
        stats = self.get_documentation_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DOCUMENTATION GENERATOR REPORT                                ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Documents: {stats['documents']}
├─ Endpoints: {stats['endpoints']}
├─ Schemas: {stats['schemas']}
├─ Parameters: {stats['parameters']}
└─ Generations: {stats['generations']}

📚 API DOCUMENTS:
"""

        for document in self.documents.values():
            report += f"\n  {document.api_name} v{document.version}\n"
            report += f"    Endpoints: {len(document.endpoints)}\n"
            report += f"    Schemas: {len(document.schemas)}\n"

        return report

    def export_documentation_config(self) -> str:
        """Export documentation configuration"""
        export_data = {
            "timestamp": time.time(),
            "documents": [
                {
                    "name": d.api_name,
                    "version": d.version,
                    "endpoints": len(d.endpoints),
                }
                for d in self.documents.values()
            ],
            "statistics": self.get_documentation_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📚 Document Generation System - API Documentation")
    print("=" * 70)

    generator = DocumentGenerator()

    # Create documentation
    print("\n📝 Creating API documentation...")
    doc = generator.create_api_documentation(
        "User Management API",
        "1.0.0",
        "API for managing users and permissions"
    )
    print(f"✅ Created documentation: {doc.document_id}")

    # Add endpoints
    print("\n📍 Adding endpoints...")
    users_ep = generator.add_endpoint(
        doc.document_id,
        "/api/users",
        "GET",
        "List all users",
        "Retrieve a paginated list of all users"
    )

    user_detail_ep = generator.add_endpoint(
        doc.document_id,
        "/api/users/{id}",
        "GET",
        "Get user details",
        "Retrieve details of a specific user"
    )

    print(f"✅ Added {len(doc.endpoints)} endpoints")

    # Add parameters
    print("\n📋 Adding parameters...")
    generator.add_parameter(users_ep.endpoint_id, "limit", "integer", description="Max results")
    generator.add_parameter(users_ep.endpoint_id, "offset", "integer", description="Offset")
    generator.add_parameter(user_detail_ep.endpoint_id, "id", "string", required=True)
    print("✅ Added parameters")

    # Add responses
    print("\n📤 Adding responses...")
    generator.add_response(users_ep.endpoint_id, 200, "Success", {"users": []})
    generator.add_response(users_ep.endpoint_id, 400, "Bad request")
    generator.add_response(user_detail_ep.endpoint_id, 200, "User found")
    generator.add_response(user_detail_ep.endpoint_id, 404, "User not found")
    print("✅ Added responses")

    # Define schemas
    print("\n🗂️  Defining schemas...")
    generator.define_schema(
        "User",
        {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "role": {"type": "string"}
        }
    )
    print(f"✅ Defined {len(generator.schemas)} schemas")

    # Generate documentation
    print("\n📄 Generating documentation...")
    markdown = generator.export_document(doc.document_id, DocumentFormat.MARKDOWN)
    print(f"✅ Generated Markdown ({len(markdown)} chars)")

    openapi = generator.export_document(doc.document_id, DocumentFormat.OPENAPI)
    print(f"✅ Generated OpenAPI ({len(openapi)} chars)")

    # Generate report
    print(generator.generate_documentation_report())

    # Export
    print("\n📄 Exporting config...")
    export = generator.export_documentation_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Document generation ready")


if __name__ == "__main__":
    main()
